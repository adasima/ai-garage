# Rust-Analyz-MCP

Rust-Analyzer を Model Context Protocol (MCP) 経由で利用できるようにするための、軽量かつ、AI エージェントの自律開発に特化したブリッジサーバーです。
ADASIM によって設計・開発されました。

AI エージェントが Rust の型システム、ドキュメント、コンパイルエラーを直接把握し、開発を爆速化させます。

## For AI Agents

エージェント（AI）がこのツールを効率的（省トークン）に使用するためのプロンプトが [SKILL.md](./SKILL.md) に用意されています。
**開発を開始する前に、必ずこのファイルを読み込んでください。**

## 特徴

- **エージェント自律最適化**: AI がシンボル探索、プロジェクト診断、参照解決を最小限のトークンで行えるよう、出力を極限まで要約します。
- **スマート自動追従 (Smart Rooting)**: 対象ファイルから適切な `Cargo.toml` を自動検出し、マルチプロジェクト環境でも設定不要で動作します。
- **環境変数不要**: 通信の安定性を最優先し、デバッグログはすべて `stderr` に隔離。`stdout` は純粋な JSON 通信のみを保証します。

## 提供されるツール (全6種)

### 1. `get_workspace_diagnostics` (推奨)
ワークスペース全体のコンパイルエラー、警告を取得し、重要なものを要約して返します。AI への「現状報告」に最適です。

### 2. `get_diagnostics`
現在開いているファイルに関連する診断情報を取得します。

### 3. `get_symbols`
指定したファイル内の構造体、関数、列挙型などの定義一覧を取得します。コードの全体像を把握するのに役立ちます。

### 4. `hover`
特定の位置にあるシンボルの型情報とドキュメントを取得します。

### 5. `get_definition`
シンボルの定義元（ファイル名、行、列）を特定します。

### 6. `get_references`
特定のシンボルがプロジェクト内のどこで使用されているか、一覧を取得します。

## セットアップ

### 0. 前提条件
- **Rust ビルドツールチェーン** ([rustup でインストール](https://rustup.rs/))
- **`rust-analyzer` コンポーネント本体** (解析エンジンとして必須)：
```powershell
rustup component add rust-analyzer
```


### 1. インストール (一発導入)

GitHub から直接リモートインストール＆ビルド・配置までを 1 コマンドで実行できます。

```powershell
cargo install --git https://github.com/adasima/rust-analyz-mcp --force
```
*(上記コマンドを実行すると、自動的に `$HOME/.cargo/bin/` に `rust-analyz-mcp.exe` が配置されます)*

### 2. 各種エージェント用の設定 (Agent Configuration)
エージェントの設定ファイル（`mcp_config.json` 等）に以下を追記するだけで動作します：
```json
"mcpServers": {
  "rust-analyz-mcp": {
    "command": "rust-analyz-mcp"
  }
}
```

### 3. 全自動インストール・設定 (全ツール一括)
全ツールを一気にインストールし、設定まで自動で行いたい場合は、以下のワンライナーを実行してください。

```powershell
Invoke-RestMethod "https://raw.githubusercontent.com/adasima/ai-workshop/main/mcp_installer.ps1" | Invoke-Expression
```
