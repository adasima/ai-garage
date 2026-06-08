use anyhow::Result;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};

#[derive(Debug, Deserialize)]
struct JsonRpcRequest {
    id: Option<Value>,
    method: String,
    params: Option<Value>,
}

#[derive(Debug, Serialize)]
struct JsonRpcResponse {
    jsonrpc: String,
    id: Value,
    #[serde(skip_serializing_if = "Option::is_none")]
    result: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<Value>,
}

#[tokio::main]
async fn main() -> Result<()> {
    let stdin = tokio::io::stdin();
    let mut reader = BufReader::new(stdin).lines();
    let mut stdout = tokio::io::stdout();

    while let Some(line) = reader.next_line().await? {
        if line.trim().is_empty() {
            continue;
        }

        let req: Result<JsonRpcRequest, _> = serde_json::from_str(&line);
        match req {
            Ok(request) => {
                if let Some(id) = request.id {
                    let result = handle_request(&request.method, request.params).await;
                    let response = match result {
                        Ok(res) => JsonRpcResponse {
                            jsonrpc: "2.0".to_string(),
                            id,
                            result: Some(res),
                            error: None,
                        },
                        Err(e) => {
                            // Simple error format
                            JsonRpcResponse {
                                jsonrpc: "2.0".to_string(),
                                id,
                                result: None,
                                error: Some(json!({
                                    "code": -32603,
                                    "message": e.to_string(),
                                })),
                            }
                        }
                    };
                    let mut res_str = serde_json::to_string(&response)?;
                    res_str.push('\n');
                    stdout.write_all(res_str.as_bytes()).await?;
                    stdout.flush().await?;
                } else {
                    // It's a notification, like "notifications/initialized"
                    if request.method == "notifications/initialized" {
                        // ignore or log
                    }
                }
            }
            Err(e) => {
                eprintln!("Failed to parse request: {}", e);
            }
        }
    }
    Ok(())
}

async fn handle_request(method: &str, params: Option<Value>) -> Result<Value> {
    match method {
        "initialize" => Ok(json!({
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "diag-struct-mcp",
                "version": "0.1.0"
            }
        })),
        "tools/list" => Ok(json!({
            "tools": [
                {
                    "name": "get_structured_diagnostics",
                    "description": "Run a linter (cargo, svelte-check, tsc) in the target directory and return structured JSON output with error messages and line numbers.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "tool": {
                                "type": "string",
                                "description": "The linter tool to run. Enum: 'cargo', 'svelte-check', 'tsc'."
                            },
                            "cwd": {
                                "type": "string",
                                "description": "The absolute path to the directory to run the tool in."
                            }
                        },
                        "required": ["tool", "cwd"]
                    }
                }
            ]
        })),
        "tools/call" => {
            let params = params.unwrap_or_else(|| json!({}));
            let tool_name = params.get("name").and_then(|v| v.as_str()).unwrap_or("");
            if tool_name == "get_structured_diagnostics" {
                let args = params.get("arguments").and_then(|v| v.as_object());
                if let Some(args) = args {
                    let tool = args.get("tool").and_then(|v| v.as_str()).unwrap_or("");
                    let cwd = args.get("cwd").and_then(|v| v.as_str()).unwrap_or("");
                    
                    let result = run_diagnostic_tool(tool, cwd).await?;
                    Ok(json!({
                        "content": [
                            {
                                "type": "text",
                                "text": serde_json::to_string(&result)?
                            }
                        ]
                    }))
                } else {
                    Err(anyhow::anyhow!("Missing arguments"))
                }
            } else {
                Err(anyhow::anyhow!("Unknown tool"))
            }
        }
        _ => Err(anyhow::anyhow!("Method not found: {}", method)),
    }
}

async fn run_diagnostic_tool(tool: &str, cwd: &str) -> Result<Value> {
    use tokio::process::Command;
    
    match tool {
        "cargo" => {
            // cargo clippy --message-format=json
            let output = Command::new("cargo")
                .arg("clippy")
                .arg("--message-format=json")
                .current_dir(cwd)
                .output()
                .await?;
            
            let stdout = String::from_utf8_lossy(&output.stdout);
            let mut diagnostics = Vec::new();
            
            for line in stdout.lines() {
                if let Ok(value) = serde_json::from_str::<Value>(line) {
                    if value.get("reason").and_then(|v| v.as_str()) == Some("compiler-message") {
                        if let Some(msg) = value.get("message") {
                            // Extract relevant fields to save tokens
                            if let Some(level) = msg.get("level").and_then(|v| v.as_str()) {
                                if level == "error" || level == "warning" {
                                    diagnostics.push(json!({
                                        "level": level,
                                        "message": msg.get("message"),
                                        "code": msg.get("code").and_then(|c| c.get("code")),
                                        "spans": msg.get("spans")
                                    }));
                                }
                            }
                        }
                    }
                }
            }
            Ok(json!({ "diagnostics": diagnostics }))
        }
        "svelte-check" => {
            // svelte-check --output machine (since json isn't native by default in older versions without standard formatting)
            let output = Command::new("svelte-check")
                .arg("--output")
                .arg("machine")
                .current_dir(cwd)
                .output()
                .await?;
                
            let stdout = String::from_utf8_lossy(&output.stdout);
            let mut diagnostics = Vec::new();
            
            for line in stdout.lines() {
                // "START" "Machine format" etc..
                // The actual error lines look like:
                // "/path/to/file.svelte" line:col error/warn "message"
                let parts: Vec<&str> = line.split('\t').collect(); // machine format is usually tab delimited or simple spaces? Sometimes it's better to just return the whole string or parse basic format.
                if parts.len() > 1 {
                    diagnostics.push(json!({"raw_line": line}));
                }
            }
            // For now, return basic lines if we just want token saving over raw terminal ansi escapes
            Ok(json!({ "diagnostics": stdout.to_string() }))
        }
        "tsc" => {
             // tsc --noEmit --pretty false
             let output = Command::new("npx")
                 .arg("tsc")
                 .arg("--noEmit")
                 .arg("--pretty")
                 .arg("false")
                 .current_dir(cwd)
                 .output()
                 .await?;
                 
             let stdout = String::from_utf8_lossy(&output.stdout);
             Ok(json!({ "diagnostics": stdout.to_string() }))
        }
        _ => Err(anyhow::anyhow!("Unsupported tool: {}", tool))
    }
}
