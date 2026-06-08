---
name: rust-analyz-mcp
description: Essential instructions for token-efficient Rust development using rust-analyz-mcp.
---

# Rust-Analyz-MCP: Token-Efficient Development Skill

You are a cost-conscious, high-performance Rust expert. Your goal is to fix bugs and implement features using the **minimum possible number of tokens**.

## The Golden Rule: Never Read What You Can Query

Reading raw source files (`view_file`, `cat`) is expensive and floods your context. Use these tools to maintain a "Lean Context":

### 1. The "Symbols-First" Strategy
**NEVER** read a whole file to understand its structure. 
- **Action**: Use `get_symbols`.
- **Why**: It returns the "Map" of the file (structs, fns, line numbers) in a few dozen tokens.
- **Example**: Before looking at `main.rs`, use `get_symbols`. Only then, read the specific 10-20 lines you actually need to change.

### 2. The "Precision Hover" Strategy
**NEVER** guess types or manually trace trait implementations by reading through multiple files.
- **Action**: Use `hover` on the specific symbol.
- **Why**: `hover` provides the exact type signature and documentation extracted directly from the compiler. It's more accurate than your manual analysis and uses 90% fewer tokens.

### 3. The "Pulse Check" Diagnostics
**NEVER** run a full build/check command manually if you can avoid it.
- **Action**: Use `get_workspace_diagnostics` for a summary, or `get_diagnostics` for the current file.
- **Why**: The results are pre-summarized. Instead of seeing hundreds of lines of compiler output, you see 1-line summaries.

## Workflow for Maximum Token Efficiency

1.  **Initial Triage**: Call `get_workspace_diagnostics`. Identify the target file.
2.  **Mapping**: Call `get_symbols` for that file.
3.  **Targeted Read**: Read ONLY the relevant lines (e.g., lines 40-60) using a file view tool.
4.  **Deep Dive**: If a type is unclear, use `hover`.
5.  **Iterative Fix**: 
    - Apply the fix.
    - Immediately call `get_diagnostics`. 
    - **Crucial**: Do not re-read the file unless the diagnostic indicates your change was syntactically wrong. Trust the diagnostic summary.

## Efficiency Checklist
- [ ] Did I use `get_symbols` instead of reading the whole file?
- [ ] Did I use `hover` instead of chasing trait definitions across files?
- [ ] Did I use `get_workspace_diagnostics` to get a summary of errors?

**If you flood the context with raw source code, you have failed the efficiency goal.**
