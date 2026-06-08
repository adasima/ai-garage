use anyhow::{Context, Result};
use lsp_types::*;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::{HashMap, HashSet};
use std::path::{Path, PathBuf};
use std::process::Stdio;
use std::sync::Arc;
use tokio::io::{AsyncBufReadExt, AsyncReadExt, AsyncWriteExt, BufReader};
use tokio::process::{ChildStdin, ChildStdout, Command};
use tokio::sync::{oneshot, Mutex};

#[derive(Serialize, Deserialize, Debug)]
struct McpRequest {
    jsonrpc: String,
    method: String,
    params: Value,
    id: Option<Value>,
}

struct State {
    pending_requests: HashMap<i64, oneshot::Sender<Value>>,
    next_id: i64,
    diagnostics: HashMap<String, Vec<Diagnostic>>,
    registered_roots: HashSet<String>,
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_writer(std::io::stderr)
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env().add_directive(tracing::Level::INFO.into()))
        .init();

    let mut ra_process = Command::new("rust-analyzer")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::inherit())
        .spawn()
        .context("Failed to spawn rust-analyzer.")?;

    let ra_stdin = Arc::new(Mutex::new(ra_process.stdin.take().unwrap()));
    let ra_stdout = ra_process.stdout.take().unwrap();
    let state = Arc::new(Mutex::new(State {
        pending_requests: HashMap::new(),
        next_id: 1,
        diagnostics: HashMap::new(),
        registered_roots: HashSet::new(),
    }));

    let state_clone = state.clone();
    tokio::spawn(async move {
        let mut reader = BufReader::new(ra_stdout);
        loop {
            if let Err(e) = handle_ra_output(&mut reader, &state_clone).await {
                tracing::error!("RA Loop error: {}", e);
                break;
            }
        }
    });

    let _ = send_ra_request(&ra_stdin, "initialize", json!({
        "processId": std::process::id(),
        "capabilities": {
            "workspace": { "workspaceFolders": true },
            "textDocument": {
                "hover": { "contentFormat": ["plaintext", "markdown"] },
                "definition": { "dynamicRegistration": false },
                "documentSymbol": { "hierarchicalDocumentSymbolSupport": true },
                "references": { "dynamicRegistration": false }
            }
        },
        "rootUri": null
    }), &state).await?;
    send_ra_notification(&ra_stdin, "initialized", json!({})).await?;

    let mut mcp_lines = BufReader::new(tokio::io::stdin()).lines();
    while let Some(line) = mcp_lines.next_line().await? {
        let req: McpRequest = match serde_json::from_str(&line) { Ok(r) => r, Err(_) => continue };
        match req.method.as_str() {
            "initialize" => {
                let res = json!({ "jsonrpc": "2.0", "id": req.id, "result": { "protocolVersion": "2024-11-05", "capabilities": { "tools": {} }, "serverInfo": { "name": "rust-analyz-mcp", "version": "0.1.0" } } });
                println!("{}", serde_json::to_string(&res)?);
            }
            "tools/list" => {
                let res = json!({ "jsonrpc": "2.0", "id": req.id, "result": { "tools": [
                    { "name": "get_diagnostics", "description": "Concise list of compiler errors.", "inputSchema": { "type": "object", "properties": {} } },
                    { "name": "get_workspace_diagnostics", "description": "Summary of all diagnostics across registered workspace roots.", "inputSchema": { "type": "object", "properties": {} } },
                    { "name": "hover", "description": "Type info and docs. Smartly finds the project root.", "inputSchema": { "type": "object", "properties": { "path": { "type": "string" }, "line": { "type": "integer" }, "column": { "type": "integer" } }, "required": ["path", "line", "column"] } },
                    { "name": "get_definition", "description": "Finds definition site.", "inputSchema": { "type": "object", "properties": { "path": { "type": "string" }, "line": { "type": "integer" }, "column": { "type": "integer" } }, "required": ["path", "line", "column"] } },
                    { "name": "get_symbols", "description": "List all symbols (structs, fns, etc) in a file.", "inputSchema": { "type": "object", "properties": { "path": { "type": "string" } }, "required": ["path"] } },
                    { "name": "get_references", "description": "Find all references to a symbol.", "inputSchema": { "type": "object", "properties": { "path": { "type": "string" }, "line": { "type": "integer" }, "column": { "type": "integer" } }, "required": ["path", "line", "column"] } }
                ] } });
                println!("{}", serde_json::to_string(&res)?);
            }
            "tools/call" => {
                let name = req.params["name"].as_str().unwrap_or("");
                let args = &req.params["arguments"];
                let path_str = args["path"].as_str().unwrap_or("");
                
                if !path_str.is_empty() {
                    if let Ok(abs_path) = std::fs::canonicalize(path_str) {
                        if let Some(root) = find_cargo_root(&abs_path) {
                            let root_uri = path_to_uri(&root);
                            let mut s = state.lock().await;
                            if !s.registered_roots.contains(&root_uri) {
                                tracing::info!("Registering root: {}", root_uri);
                                s.registered_roots.insert(root_uri.clone());
                                drop(s);
                                let _ = send_ra_notification(&ra_stdin, "workspace/didChangeWorkspaceFolders", json!({
                                    "event": { "added": [{ "uri": root_uri, "name": root.file_name().unwrap_or_default().to_string_lossy() }], "removed": [] }
                                })).await;
                                tokio::time::sleep(tokio::time::Duration::from_millis(200)).await;
                            }
                        }
                    }
                }

                let result = match name {
                    "get_diagnostics" | "get_workspace_diagnostics" => {
                        let s = state.lock().await;
                        let mut text = String::new();
                        let mut count = 0;
                        for (uri, items) in &s.diagnostics {
                            let file = uri.split('/').last().unwrap_or(uri);
                            for d in items {
                                let sev = match d.severity { Some(DiagnosticSeverity::ERROR) => "ERR", Some(DiagnosticSeverity::WARNING) => "WRN", _ => "INF" };
                                text.push_str(&format!("{}:{}:{} [{}] {}\n", file, d.range.start.line + 1, d.range.start.character + 1, sev, d.message));
                                count += 1;
                            }
                        }
                        if count > 50 { text = format!("(Showing first 50 of {} diagnostics)\n{}", count, text.lines().take(50).collect::<Vec<_>>().join("\n")); }
                        json!({ "content": [{ "type": "text", "text": if text.is_empty() { "No issues.".into() } else { text } }] })
                    }
                    "hover" | "get_definition" | "get_symbols" | "get_references" => {
                        let line = args["line"].as_u64().unwrap_or(0);
                        let col = args["column"].as_u64().unwrap_or(0);
                        let uri = if let Ok(abs) = std::fs::canonicalize(path_str) { path_to_uri(&abs) } else { format!("file:///{}", path_str.replace("\\", "/")) };
                        
                        let lsp_method = match name {
                            "hover" => "textDocument/hover",
                            "get_definition" => "textDocument/definition",
                            "get_symbols" => "textDocument/documentSymbol",
                            "get_references" => "textDocument/references",
                            _ => "",
                        };
                        
                        let lsp_params = if name == "get_symbols" {
                            json!({ "textDocument": { "uri": uri } })
                        } else if name == "get_references" {
                            json!({ "textDocument": { "uri": uri }, "position": { "line": line, "character": col }, "context": { "includeDeclaration": true } })
                        } else {
                            json!({ "textDocument": { "uri": uri }, "position": { "line": line, "character": col } })
                        };

                        let res = send_ra_request(&ra_stdin, lsp_method, lsp_params, &state).await?;
                        let mut out = String::new();
                        
                        match name {
                            "hover" => {
                                if let Some(contents) = res.get("contents") {
                                    match contents {
                                        Value::String(s) => out.push_str(s),
                                        Value::Object(obj) => { if let Some(v) = obj.get("value").and_then(|v| v.as_str()) { out.push_str(v); } }
                                        Value::Array(arr) => { for i in arr { if let Some(s) = i.as_str() { out.push_str(s); out.push_str("\n"); } else if let Some(v) = i.get("value").and_then(|v| v.as_str()) { out.push_str(v); out.push_str("\n"); } } }
                                        _ => { if let Ok(s) = serde_json::to_string(&contents) { out.push_str(&s); } }
                                    }
                                }
                            }
                            "get_definition" | "get_references" => {
                                if let Some(arr) = res.as_array() { for l in arr { let u = l["uri"].as_str().unwrap_or(""); let s = &l["range"]["start"]; out.push_str(&format!("{} L{}:C{}\n", u, s["line"].as_u64().unwrap_or(0)+1, s["character"].as_u64().unwrap_or(0)+1)); } }
                                else if let Some(l) = res.as_object() { let u = l["uri"].as_str().unwrap_or(""); let s = &l["range"]["start"]; out.push_str(&format!("{} L{}:C{}\n", u, s["line"].as_u64().unwrap_or(0)+1, s["character"].as_u64().unwrap_or(0)+1)); }
                            }
                            "get_symbols" => {
                                if let Some(arr) = res.as_array() {
                                    parse_symbols(arr, &mut out, 0);
                                }
                            }
                            _ => {}
                        }
                        
                        json!({ "content": [{ "type": "text", "text": if out.is_empty() { "No data found.".into() } else { out } }] })
                    }
                    _ => json!({ "isError": true, "content": [{ "type": "text", "text": "Tool not found" }] })
                };
                println!("{}", serde_json::to_string(&json!({ "jsonrpc": "2.0", "id": req.id, "result": result }))?);
            }
            _ => {}
        }
    }
    Ok(())
}

fn path_to_uri(path: &Path) -> String {
    let s = path.to_string_lossy().replace("\\", "/");
    let s = s.trim_start_matches("//?/");
    format!("file:///{}", s)
}

fn parse_symbols(values: &Vec<Value>, out: &mut String, depth: usize) {
    for s in values {
        let name = s["name"].as_str().unwrap_or("?");
        let kind = match s["kind"].as_u64().unwrap_or(0) { 1=>"File", 5=>"Struct", 6=>"Method", 12=>"Function", 13=>"Variable", 23=>"Enum", _=>"Symbol" };
        let start = &s["selectionRange"]["start"]; // Using selectionRange for better precision
        let indent = "  ".repeat(depth);
        out.push_str(&format!("{}- [{}] {} (L{}:C{})\n", indent, kind, name, start["line"].as_u64().unwrap_or(0)+1, start["character"].as_u64().unwrap_or(0)+1));
        if let Some(children) = s["children"].as_array() {
            parse_symbols(children, out, depth + 1);
        }
    }
}

fn find_cargo_root(path: &Path) -> Option<PathBuf> {
    let mut current = if path.is_file() { path.parent()? } else { path };
    loop {
        if current.join("Cargo.toml").exists() { return Some(current.to_path_buf()); }
        current = current.parent()?;
    }
}

async fn handle_ra_output(reader: &mut BufReader<ChildStdout>, state: &Arc<Mutex<State>>) -> Result<()> {
    let mut line = String::new();
    if reader.read_line(&mut line).await? == 0 { return Ok(()); }
    if !line.starts_with("Content-Length:") { return Ok(()); }
    let len: usize = line.trim_start_matches("Content-Length:").trim().parse()?;
    let mut empty = String::new(); reader.read_line(&mut empty).await?;
    let mut body = vec![0u8; len]; reader.read_exact(&mut body).await?;
    let json: Value = serde_json::from_slice(&body)?;
    if let Some(method) = json["method"].as_str() {
        if method == "textDocument/publishDiagnostics" {
            let mut s = state.lock().await;
            let uri = json["params"]["uri"].as_str().unwrap_or("").to_string();
            let ds: Vec<Diagnostic> = serde_json::from_value(json["params"]["diagnostics"].clone()).unwrap_or_default();
            s.diagnostics.insert(uri, ds);
        }
    } else if let Some(id) = json["id"].as_i64() {
        let mut s = state.lock().await;
        if let Some(tx) = s.pending_requests.remove(&id) {
            let _ = tx.send(if json.get("error").is_some() { json["error"].clone() } else { json.get("result").cloned().unwrap_or(Value::Null) });
        }
    }
    Ok(())
}

async fn send_ra_request(stdin: &Arc<Mutex<ChildStdin>>, method: &str, params: Value, state: &Arc<Mutex<State>>) -> Result<Value> {
    let id = { let mut s = state.lock().await; s.next_id += 1; s.next_id };
    let (tx, rx) = oneshot::channel();
    state.lock().await.pending_requests.insert(id, tx);
    let req = json!({ "jsonrpc": "2.0", "id": id, "method": method, "params": params });
    let s = serde_json::to_string(&req)?;
    let msg = format!("Content-Length: {}\r\n\r\n{}", s.len(), s);
    let mut lock = stdin.lock().await;
    lock.write_all(msg.as_bytes()).await?; lock.flush().await?;
    Ok(rx.await.unwrap_or(Value::Null))
}

async fn send_ra_notification(stdin: &Arc<Mutex<ChildStdin>>, method: &str, params: Value) -> Result<()> {
    let req = json!({ "jsonrpc": "2.0", "method": method, "params": params });
    let s = serde_json::to_string(&req)?;
    let msg = format!("Content-Length: {}\r\n\r\n{}", s.len(), s);
    let mut lock = stdin.lock().await;
    lock.write_all(msg.as_bytes()).await?; lock.flush().await?;
    Ok(())
}
