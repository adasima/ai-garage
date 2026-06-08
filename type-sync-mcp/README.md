# Type-Sync Bridge (type-sync-mcp)

Rust の AST パース (`syn` クレート) を用いてネイティブに構造体の定義を抽出し、ローカルで安全に TypeScript のインターフェースへと変換する Model Context Protocol (MCP) サーバーです。特に Svelte や Tauri を用いたハイブリッドアプリケーション開発で絶大な威力を発揮します。

## AI エージェントへの注意事項
このツールの最適なプロンプトと使用方法は [SKILL.md](./SKILL.md) (英語) に記載されていますので、必ず従ってください。

## 特徴
- **ハルシネーション・ゼロ**: 単なる推測ではなく、厳格な AST 解析を用いて型をマッピングします。
- **Serde 属性のスマート検出**: `#[serde(rename_all="camelCase")]` や `#[serde(skip_serializing_if)]` などの設定を自動で検出し、バックエンドとフロントエンド間の型と命名のズレを完璧に防ぎます。

## セットアップ

### 0. 前提条件
- **Rust ビルドツールチェーンのみ** ([rustup でインストール](https://rustup.rs/))
※ 独自解析エンジンを完全内蔵しているため、他ツールの事前インストールは一切不要です！

### 1. インストール (一発導入)

GitHub から直接リモートインストール＆ビルド・配置までを 1 コマンドで実行できます。

```powershell
cargo install --git https://github.com/adasima/type-sync-mcp
```
*(上記コマンドを実行すると、自動的に `$HOME/.cargo/bin/` に `type-sync-mcp.exe` が配置されます)*

### 2. 各種エージェント用の設定 (Agent Configuration)

#### Claude Desktop
設定ファイル: `%APPDATA%\Claude\claude_desktop_config.json`
```json
"mcpServers": {
  "type-sync-mcp": {
    "command": "type-sync-mcp"
  }
}
```
*(事前に `cargo install --git https://github.com/adasima/type-sync-mcp --force` を実行してください)*
