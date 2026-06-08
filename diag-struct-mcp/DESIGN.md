# Diagnostic Structurizer MCP (`diag-struct-mcp`)

## 目的
`cargo clippy`, `svelte-check`, `tsc` といったツールからの標準出力をJSON形式（構造化データ）に変換し、AIがエラー箇所を機械的に特定できるようにする。

## 提供する機能 (Tools)
- `get_structured_diagnostics`: 任意の Linter/Checker ツールを実行し、ファイルパス・行数・エラーメッセージ・修正提案を含む JSON 配列を返す。

## 実装方針
- 各種ツールの標準出力・標準エラー出力を受け取るサブプロセスを実行する。
- ログを正規表現等でパースする、またはツール固有のJSON出力モード(`cargo clippy --message-format=json`等)を解釈して汎用フォーマットに変換する。
- 深刻なエラー（Error）のみ通知するなどのフィルタリングオプションを持たせる。
