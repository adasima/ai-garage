# Type-Sync Bridge MCP (`type-sync-mcp`)

## 目的
Rustのバックエンド（Tauri・Axum等）とTypeScriptのフロントエンド間で型定義を安全かつ自動的に同期・検証する。
AIエージェントが型安全性を確保しつつ、不要なファイルの直接参照を避けるためのツールです。

## 提供する機能 (Tools)
- `check_type_drift`: 指定されたRustの構造体とTS側のインターフェースの差分を検知する。
- `generate_ts_interface`: Rustのファイルから型定義を生成し、TS向けに整形して出力（または該当ファイルを上書き）する。

## 実装方針
- Rustの `syn` クレートを利用してASTから構造体フィールドの型情報や属性を抽出する。
- ターゲット言語は初期段階で TypeScript に特化。
- 出力は構造化データとし、AIエージェントのトークン節約に貢献する。
