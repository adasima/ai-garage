# Repo Topology (repo-topology-mcp)

プロジェクト環境のディレクトリ構造・ファイル構成を並外れた速度でマッピングし、AIのトークナイザーの限界に最適化された形で「ツリー表現のアーキテクチャ」を出力する Model Context Protocol (MCP) サーバーです。

## AI エージェントへの注意事項
このツールの最適なプロンプトと使用方法は [SKILL.md](./SKILL.md) (英語) に記載されていますので、必ず従ってください。

## 特徴
- **自動化された Gitignore エコシステム**: `ripgrep` のコアでもある Rust の公式 `ignore` クレートを利用。手動設定不要で `node_modules` や `target` を勝手に無視し、ハルシネーション（不要なディープダイブ）を防ぎます。
- **インテリジェント・エコモード**: コマンドラインの `tree` を模した形式を用いて、JSON の冗長なトークン消費を大幅カット。大きな画像アセット群などは `[25 files...]` のように自動圧縮してコンテキストウィンドウの使用量を極限まで抑えます。

## セットアップ

### 0. 前提条件
- **Rust ビルドツールチェーンのみ** ([rustup でインストール](https://rustup.rs/))
※ 独自解析エンジンを完全内蔵しているため、他ツールの事前インストールは一切不要です！


### 1. インストール (一発導入)

GitHub から直接リモートインストール＆ビルド・配置までを 1 コマンドで実行できます。

```powershell
cargo install --git https://github.com/adasima/repo-topology-mcp --force
```
*(上記コマンドを実行すると、自動的に `$HOME/.cargo/bin/` に `repo-topology-mcp.exe` が配置されます)*

### 2. 各種エージェント用の設定 (Agent Configuration)
エージェントの設定ファイル（`mcp_config.json` 等）に以下を追記するだけで動作します：
```json
"mcpServers": {
  "repo-topology-mcp": {
    "command": "repo-topology-mcp"
  }
}
```

### 3. 全自動インストール・設定 (全ツール一括)
全ツールを一気にインストールし、設定まで自動で行いたい場合は、以下のワンライナーを実行してください。

```powershell
Invoke-RestMethod "https://raw.githubusercontent.com/adasima/ai-workshop/main/mcp_installer.ps1" | Invoke-Expression
```
