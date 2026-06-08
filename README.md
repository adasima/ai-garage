# ai-garage

ほぼ放置している、あるいはたまにいじる程度の古いAI関連・その他開発プロジェクトをまとめた物置（ガレージ）です。

## 収録プロジェクト一覧

このリポジトリには、以下のプロジェクトがサブフォルダとして統合されています。

| プロジェクト名 | 概要 | 開発言語 / 技術 | 元のURL |
| :--- | :--- | :--- | :--- |
| [repo-topology-mcp](./repo-topology-mcp) | リポジトリのトポロジー（構造）を解析・視覚化するMCPサーバー | Rust | [repo-topology-mcp](https://github.com/adasima/repo-topology-mcp) |
| [type-sync-mcp](./type-sync-mcp) | TypeScriptなどの型定義を同期するためのMCPサーバー | TypeScript | [type-sync-mcp](https://github.com/adasima/type-sync-mcp) |
| [diag-struct-mcp](./diag-struct-mcp) | コードの構造やダイアグラム解析に関連するMCPサーバー | Rust | [diag-struct-mcp](https://github.com/adasima/diag-struct-mcp) |
| [openclaw_setup_bat](./openclaw_setup_bat) | OpenClawのセットアップや初期設定を行うためのバッチスクリプト | Batchfile | [openclaw_setup_bat](https://github.com/adasima/openclaw_setup_bat) |
| [114514track](./114514track) | 音楽トラックやログデータを追跡・管理するツール | TypeScript | [114514track](https://github.com/adasima/114514track) |
| [dynamic-universe](./dynamic-universe) | Webアプリケーション of デモプロジェクト（GitHub Pagesホスト対象） | JavaScript | [dynamic-universe](https://github.com/adasima/dynamic-universe) |
| [AInoMIMI](./AInoMIMI) | AIの耳（入力・認識など）に関連するPythonプロジェクト | Python | [AInoMIMI](https://github.com/adasima/AInoMIMI) |
| [rust-analyz-mcp](./rust-analyz-mcp) | Rust解析関連のMCPサーバー | Rust | [rust-analyz-mcp](https://github.com/adasima/rust-analyz-mcp) |
| [enko](./enko) | プライベート開発プロジェクト（非公開） | - | [enko](https://github.com/adasima/enko) |

## GitHub Pages 公開ページ

`dynamic-universe` のデモWebアプリは、GitHub Actionsの自動化ワークフローを利用して以下のサブパスで公開されています。

* **デモURL**: [https://adasima.github.io/ai-garage/dynamic-universe/](https://adasima.github.io/ai-garage/dynamic-universe/)

---

## 運用の手引き (開発再開時の手順)

このリポジトリ内の個別プロジェクトを開発・編集する際は、以下のいずれかの方法で行います。

### 方法1. 全体をクローンして特定フォルダを開く（推奨・最も簡単）
1. リポジトリ全体を通常通りクローンします。
   ```bash
   git clone https://github.com/adasima/ai-garage.git
   ```
2. VS Codeなどのエディタで、開発したいサブフォルダ（例：`./114514track`）を**直接「フォルダを開く」で開いて**作業を開始します。

### 方法2. 特定のフォルダだけを部分的にクローンする (Sparse Checkout)
ディスク容量や余計なファイルをローカルに落とすのを節約したい場合に有効です。
1. 最小限の構成でクローンします。
   ```bash
   git clone --filter=blob:none --sparse https://github.com/adasima/ai-garage.git
   cd ai-garage
   ```
2. 開発したいフォルダのみを指定してダウンロードします。
   ```bash
   git sparse-checkout set <フォルダ名> (例: 114514track)
   ```
