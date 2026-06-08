# OpenClaw Sandbox Setup

Windows Sandbox 環境への [OpenClaw](https://openclaw.ai/) の自動デプロイとセットアップを簡略化するバッチスクリプトです。ローカルの LM Studio 等、OpenAI 互換のカスタムプロバイダとの連携を前提としています。

Windows Sandbox 特有の制限（`winget` が使えない、一部の環境変数が異なる、ビルドツールがない等）に対応した設計になっています。

## 特徴
- 必要な依存関係（Git, Node.js）の自動ダウンロードとサイレントインストール
- `npm` のビルドエラーを回避する `--ignore-scripts` を使用した安全な OpenClaw インストール
- Onboarding Wizard (`openclaw onboard`) の完全自動化
- Discord Bot トークンの自動設定
- ゲートウェイの自動起動と Web UI のブラウザ自動オープン
- 詳細なログ出力

## 使い方

1. このリポジトリを適当なフォルダにクローンまたはダウンロードします。
2. `setup_openclaw_sandbox_template.bat` をコピーして **`setup_openclaw_sandbox.bat`** にリネームします。（※ このファイルは `.gitignore` で除外されているため、安全にトークンなどを記述できます）
3. 作成した `setup_openclaw_sandbox.bat` をテキストエディタで開き、以下の **Settings** ブロックを環境に合わせて書き換えてください。

```bat
:: ---- Settings ------------------------------------------------
:: ★ Sandbox環境から見たホストOSのIPアドレスに変更してください
set "HOST_IP=192.168.x.x"
set "LMS_PORT=1234"
set "LMS_MODEL=qwen3.5-9b@q4_k_m"
set "OPENCLAW_PORT=18789"
:: ★ Discord Bot Token（空欄ならDiscord設定をスキップします）
set "DISCORD_BOT_TOKEN="
:: ★ Gateway Token（Control UIの認証パスワードのようなもの）
set "GATEWAY_TOKEN=my-secure-token-1234"
:: --------------------------------------------------------------
```

4. 変更を保存後、Windows Sandbox に `setup_openclaw_sandbox.bat` をコピーして実行します。
5. 全工程が自動で進行し、完了するとブラウザで OpenClaw Control UI が開きます。

## 再起動用バッチ (start_openclaw.bat) について

インストール完了後に誤ってウィンドウを閉じてしまった場合や、一旦 Sandbox の状態を維持したままプロセスが落ちた場合に、以下のような `start_openclaw.bat` を手元に作成しておくと素早く起動し直すことができます。

```bat
@echo off
set "OPENCLAW_PORT=18789"
set "GATEWAY_TOKEN=my-secure-token-1234"
set "PATH=%PATH%;%APPDATA%\npm;%ProgramFiles%\nodejs"
start "OpenClaw Gateway" cmd /k "openclaw gateway --port %OPENCLAW_PORT%"
timeout /t 5 /nobreak > nul
start "" "http://127.0.0.1:%OPENCLAW_PORT%/?token=%GATEWAY_TOKEN%"
exit /b 0
```

## 注意事項
- **LM Studio の設定:** LM Studio 側で「Serve on Local Network」をオンにしておく必要があります。
- **セキュリティ:** `DISCORD_BOT_TOKEN` のような機密情報は Git リモートにプッシュしないように注意してください。 `.gitignore` に含まれているファイル名で運用することを強く推奨します。
