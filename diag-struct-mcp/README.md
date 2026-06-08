# Diagnostic Structurizer (diag-struct-mcp)

重いローカル CLI チェッカー（`cargo clippy`、`svelte-check`、`tsc`）を実行し、その膨大なターミナルログを AI エージェント専用のクリーンで構造化された JSON フォーマットに変換する Model Context Protocol (MCP) サーバーです。

## AI エージェントへの注意事項
このツールの最適なプロンプトと使用方法は [SKILL.md](./SKILL.md) (英語) に記載されていますので、必ず従ってください。

## 特徴
- **トークン消費の極限最適化**: 生のターミナルトレースバックをそのまま流し込んでコンテキスト枠を壊すことを完全に防止。
- **統合インターフェース**: 複数の言語/フレームワークのリンターを、単一のエラー抽出パイプラインとして扱えます。

## セットアップ

### 0. 前提条件
- **Rust ビルドツールチェーン** ([rustup でインストール](https://rustup.rs/))
- **Node.js & npm** (JS/TS/Svelte を解析する場合)
※対象プロジェクトにツールが組み込まれていない場合、以下を1行実行してください：
```powershell
npm install -g typescript svelte-check
```


### 1. インストール (一発導入)

GitHub から直接リモートインストール＆ビルド・配置までを 1 コマンドで実行できます。

```powershell
cargo install --git https://github.com/adasima/diag-struct-mcp --force
```
*(上記コマンドを実行すると、自動的に `$HOME/.cargo/bin/` に `diag-struct-mcp.exe` が配置されます)*

### 2. 各種エージェント用の設定 (Agent Configuration)
エージェントの設定ファイル（`mcp_config.json` 等）に以下を追記するだけで動作します：
```json
"mcpServers": {
  "diag-struct-mcp": {
    "command": "diag-struct-mcp"
  }
}
```

### 3. 全自動インストール・設定 (全ツール一括)
全ツールを一気にインストールし、設定まで自動で行いたい場合は、以下のワンライナーを実行してください。

```powershell
Invoke-RestMethod "https://raw.githubusercontent.com/adasima/ai-workshop/main/mcp_installer.ps1" | Invoke-Expression
```
