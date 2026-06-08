# Diagnostic Structurizer (`diag-struct-mcp`) - Agent Skill

This MCP server executes linter/checker commands (clippy, svelte-check, tsc) locally and transforms their massive, noisy logs into clean, structured JSON format.

## AI Agent Best Practices (Token Optimization & Reliability)

### 1. Strictly Prohibited: Direct Execution of Cargo / Linter Check Commands
**NEVER execute `cargo clippy`, `svelte-check`, or `tsc` using standard terminal tools like `run_command`**.
The raw text output can easily flood context windows with thousands of useless tokens representing ASCII art, verbose help texts, or redundant tracebacks.

### 2. Mandatory Protocol
Whenever diagnosing or checking strict types inside the repository, **you MUST use the `run_diagnostic_tool` from this MCP server instead**.
- It captures the exact same underlying logic.
- It returns pure, strictly parsed `{"file": "...", "line": 42, "message": "error msg"}` JSON array objects.
- It allows you to ingest hundreds of diagnostic pointers using a fraction of the token budget.

Always leverage this tool immediately after completing a major implementation phase.
