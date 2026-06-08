# Type-Sync Bridge (`type-sync-mcp`) - Agent Skill

This MCP server securely reads Rust structs and enums via strict AST parsing and magically transforms them into ready-to-inject TypeScript interfaces.

## AI Agent Best Practices

1. **Say No to Hallucinations**: Do NOT attempt to manually guess or translate complex Rust structs to TypeScript interfaces mentally. Translating optional layers or custom Serde names by yourself often leads to obscure frontend bugs.
2. **Execute This Tool Before Frontend Typing**: Use `extract_ts_types_from_rust` to target any `dto.rs` or `state.rs` file.
3. **Smart Serde Reflection**: This tool automatically reads `#[serde(rename_all = "camelCase")]`, `rename="X"`, and properly converts `Option<T>` natively into `field?: Type` vs `field: Type | null`.
4. **Action Required**: This is a read-only tool. The tool will return the correctly mapped TypeScript snippet. YOU must use your `replace_file_content` or standard tools to apply the output to the relevant `.ts` interface files.
