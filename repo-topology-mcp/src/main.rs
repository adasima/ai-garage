use anyhow::{Context, Result};
use ignore::WalkBuilder;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::BTreeMap;
use std::path::{Path, PathBuf};
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

#[derive(Debug)]
struct TreeNode {
    is_dir: bool,
    children: BTreeMap<String, TreeNode>,
}

impl TreeNode {
    fn new(is_dir: bool) -> Self {
        Self {
            is_dir,
            children: BTreeMap::new(),
        }
    }
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

        match serde_json::from_str::<JsonRpcRequest>(&line) {
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
                        Err(e) => JsonRpcResponse {
                            jsonrpc: "2.0".to_string(),
                            id,
                            result: None,
                            error: Some(json!({
                                "code": -32603,
                                "message": e.to_string(),
                            })),
                        },
                    };
                    let mut res_str = serde_json::to_string(&response)?;
                    res_str.push('\n');
                    let _ = stdout.write_all(res_str.as_bytes()).await;
                    let _ = stdout.flush().await;
                }
            }
            Err(e) => {
                eprintln!("Parse error: {}", e);
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
                "name": "repo-topology-mcp",
                "version": "0.1.0"
            }
        })),
        "tools/list" => Ok(json!({
            "tools": [
                {
                    "name": "get_project_tree",
                    "description": "Get an optimized directory tree representation of the project space. Intelligently respects .gitignore.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Absolute path to the root directory to map"
                            },
                            "depth": {
                                "type": "number",
                                "description": "Maximum depth to parse. Recommend 3 or 4."
                            },
                            "detailed": {
                                "type": "boolean",
                                "description": "If true, displays all files. If false, compresses massive blocks of similar files into a summary string to save tokens (Eco Mode)."
                            }
                        },
                        "required": ["path", "depth", "detailed"]
                    }
                }
            ]
        })),
        "tools/call" => {
            let params = params.unwrap_or_else(|| json!({}));
            let tool_name = params.get("name").and_then(|v| v.as_str()).unwrap_or("");
            if tool_name == "get_project_tree" {
                let args = params.get("arguments").and_then(|v| v.as_object());
                if let Some(args) = args {
                    let path = args.get("path").and_then(|v| v.as_str()).unwrap_or("");
                    let depth = args.get("depth").and_then(|v| v.as_u64()).map(|d| d as usize);
                    let detailed = args.get("detailed").and_then(|v| v.as_bool()).unwrap_or(false);
                    
                    let tree_text = build_topology(path, depth, detailed)?;
                    
                    Ok(json!({
                        "content": [
                            {
                                "type": "text",
                                "text": tree_text
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

fn build_topology(root_path_str: &str, depth: Option<usize>, detailed: bool) -> Result<String> {
    let mut builder = WalkBuilder::new(root_path_str);
    builder.max_depth(depth);
    builder.hidden(false); // Enable looking inside hidden folders (like .github) since ignore crate still respects .gitignore
    
    let mut root_node = TreeNode::new(true);

    let base_path = Path::new(root_path_str);

    for result in builder.build() {
        if let Ok(entry) = result {
            let path = entry.path();
            if path == base_path {
                continue;
            }
            if let Ok(relative) = path.strip_prefix(base_path) {
                insert_path(&mut root_node, relative, entry.file_type().map(|ft| ft.is_dir()).unwrap_or(false));
            }
        }
    }

    let mut output = String::new();
    let abs_name = base_path.file_name().and_then(|o| o.to_str()).unwrap_or(root_path_str);
    output.push_str(&format!("{}/\n", abs_name));
    format_tree_node(&root_node, "", &mut output, detailed);

    Ok(output)
}

fn insert_path(root: &mut TreeNode, path: &Path, is_dir: bool) {
    let mut current = root;
    let components: Vec<&std::ffi::OsStr> = path.iter().collect();
    
    for (i, comp) in components.iter().enumerate() {
        let name = comp.to_string_lossy().to_string();
        let is_last = i == components.len() - 1;
        
        let node_is_dir = if is_last { is_dir } else { true };
        
        // Use entry to traverse or create
        current = current.children.entry(name).or_insert_with(|| TreeNode::new(node_is_dir));
    }
}

fn format_tree_node(node: &TreeNode, prefix: &str, output: &mut String, detailed: bool) {
    let keys: Vec<String> = node.children.keys().cloned().collect();
    let child_count = keys.len();

    // Eco-mode squashing logic
    if !detailed && child_count > 10 {
        // If they are all files (no subdirs), squash them
        let all_files = keys.iter().all(|k| !node.children.get(k).unwrap().is_dir);
        if all_files {
            output.push_str(&format!("{}└── [{} files...]\n", prefix, child_count));
            return;
        }
    }

    for (i, key) in keys.iter().enumerate() {
        let is_last = i == child_count - 1;
        let child = node.children.get(key).unwrap();

        let branch = if is_last { "└── " } else { "├── " };
        let name_suffix = if child.is_dir { "/" } else { "" };
        
        output.push_str(&format!("{}{}{}{}\n", prefix, branch, key, name_suffix));

        if child.is_dir {
            let next_prefix = format!("{}{}", prefix, if is_last { "    " } else { "│   " });
            format_tree_node(child, &next_prefix, output, detailed);
        }
    }
}
