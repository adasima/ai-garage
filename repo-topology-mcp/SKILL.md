# Repo Topology (`repo-topology-mcp`) - Agent Skill

This MCP server provides an optimized, token-efficient architectural map (directory and file tree) of a target project specifically designed for AI agents.

## AI Agent Best Practices (Eco-Operations Setup)

### 1. Default (Eco) Mode
The tool naturally compresses large clusters of static assets or boilerplate into `[ X files... ]` summaries to protect your context window.
**Use this tool heavily upon first entering a novel project** or to understand massive architecture changes without spending thousands of standard directory tokens. By default, it operates completely out-of-the-box using the target project's `.gitignore` rules (never flooding the context with `node_modules` or `.git`).

### 2. Full Diagnostics Mode
If you explicitly require scanning exact filenames inside deep asset folders or auto-compressed modules, pass parameter `detailed: true`.
Use this restrictively during complex system-wide refactors where scanning every explicit file is strategically necessary.

### 3. Tree Constraints
Always supply a sensible `depth` parameter (recommended: 3 to 4 branches down) to prevent scanning enormous legacy architectures indefinitely.
