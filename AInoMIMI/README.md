# AINOMIMI: The Critic - 音楽解析パイプライン

AIを用いて楽曲を分離・解析し、音楽評論家のようなレポートとMIDIデータを生成するツールです。

## 🐣 このツールでできること（初心者向け）

専門的な知識がなくても、お気に入りの曲を「深く知る」ための機能が詰まっています。

- **1. 楽器をバラバラにする**: ボーカルだけ、ドラムだけ、といった形に音源をきれいに分離します。
- **2. 自動で歌詞を書き起こす**: 歌声を認識して、AIが自動で歌詞をテキストにします。
- **3. 「音楽評論家」の解説**: 曲の雰囲気やボーカルの歌い方のクセ、曲の盛り上がりどころをAIが分析して、日本語のレポートにまとめてくれます。
- **4. 楽譜データ（MIDI）を作る**: メロディやコード進行をデータ化し、DTMソフトで使える形式で保存できます。
- **5. 自分だけの音楽図鑑**: 一度解析した曲はライブラリに保存され、いつでも見返すことができます。
- **6. 声・音の個性を数値化**: 16軸のプロファイリングにより、「アイドル声」「宝塚ボーイッシュ」「ロックシャウター」等の特徴を定量データとして可視化します。

---

## 🏗 構成・アーキテクチャ

本プロジェクトは、以下のフェーズで動作するパイプライン構造を採用しています。

### 1. Phase 1: 分離 (The Surgeon)
- **担当**: `modules/surgeon.py` / `modules/roformer_runner.py`
- **モデル**: 
    - **Standard**: Demucs (`htdemucs_6s` — 6ステムモデル)
    - **Hybrid**: BS-Roformer (Vocal/Inst) + Demucs (Other stems)
- **内容**: 元の音源を「Vocal, Bass, Drums, Guitar, Piano, Other」の各ステムに分離します。
- **特徴**:
    - **Hybrid Mode**: ボーカル分離にSDR ~13dBを誇る `BS-Roformer` を使用し、圧倒的なクリアさを実現。
    - **Iterative Blending**: 分離結果を複数回ブレンドすることで、微細なアーティファクトを除去するオプション。
    - `torchcodec` の問題を回避するためのWAV事前変換処理。
    - VRAM解放（GC / EmptyCache）による省メモリ動作。
    - 無音トラックの自動除外（-75dB以下を削除）。

### 2. Phase 2: 解析 (The Analysts)
- **担当**: `modules/analyst.py`
- **内容**: 各ステムから音楽学的および言語的データを抽出します。
- **抽出項目**:
    - **基本特徴**: BPM, RMS（音量）, スペクトル輝度, 持続時間。
    - **調性解析**: Krumhansl-Kesslerプロファイルによるキー/スケール推定（例: C Major）。
    - **LUFS**: RMSベースの知覚音圧レベル推定。
    - **リズムパターン**: onset_strengthの自己相関によるリズム分類（4つ打ち/バックビート/シャッフル等）。
    - **歌唱・言語**: Whisperによる歌詞転記とタイムスタンプ抽出。
    - **和声・旋律**: `pyin` によるメロディ抽出、Chroma特徴量によるコード進行推定。
    - **AudioSet分類**: MIT/AST (527クラス) によるジャンル・楽器・エフェクトの詳細検出。
    - **音色解析**: EQバランス、ダイナミックレンジ、空間特性の数値化。
    - **ボーカルスタイル**: 息成分、ダイナミクス変動からの歌唱スタイル自動判定。

### 2.5. マスター音源全体解析
- **担当**: `modules/analyst.py` (`analyze_master_mix`)
- **内容**: Stem分離前の2mix原曲にAudioSet + librosa基本特徴量を適用。
- **目的**: ステム単体では失われる「アンサンブルとしてのジャンル感・グルーヴ」を回収。

### 3. Phase 3: プロファイリング (The Profiler)
- **担当**: `modules/profiler.py`
- **内容**: 解析データを統合し、16軸の汎用音声プロファイルを生成。
- **軸構成**:
    - **インスト8軸**: テンポ感 / キラキラ・輝度 / ビート安定度 / Pop適合度 / 華やかさ / 重厚感 / 電子感 / 生演奏感
    - **ボーカル8軸**: 声の明るさ / 息遣い / 音程安定度 / 声域の高さ / パワー / 軽やかさ / ビブラート強度 / 音域幅
- **特徴**:
    - 軸定義は辞書ベース（追加・削除はコード変更不要）。
    - `combined_signature`: LLMに渡して具体的キャラ名やアーティスト名を想起させるための詳細テキスト自動生成。
    - レーダーチャート用データ構造を自動出力。

### 4. Phase 4: 統合・解釈 (The Critic)
- **担当**: `modules/exporter.py` / `modules/summarizer.py`
- **内容**: 解析された「数値データ」を、「音楽評論」として再構築します。
- **機能**:
    - **マスター音源サマリー**: 全体のテンポ/キー/LUFS/リズム/ジャンルを一覧表示。
    - **世界観分析**: 歌詞の感情と曲調の組み合わせによる作品背景の推定。
    - **ボーカルプロファイリング**: 声質（息漏れ、粗さ）や歌唱スタイルの言語化。
    - **構成推定**: 音量ダイナミクスに基づくサビ（盛り上がり）区間の自動検出。
    - **トラック別ジャンル最適化**: 全体と異なるステムのみジャンル表示（冗長さ排除）。
    - **プロファイルセクション**: ASCIIバーチャート + 統合シグネチャによるプロファイル可視化。
    - **MIDI生成**: 抽出したメロディやコードデータをマルチトラックMIDIとして書き出し。

### 5. Phase 5: インターフェース (UI/UX)
- **担当**: `gui.py`
- **内容**: `customtkinter` を用いたダッシュボード。
- **機能**:
    - **分離設定**: GUI上で `Standard / Hybrid` モードの切替や、反復ブレンド回数(2-4パス)を即座に変更可能。
    - **スレッド実行**: メインスレッドをブロックしない非同期処理による応答性の高い解析。
    - **ライブラリ管理**: `output/` 内を自動スキャンし、過去の解析結果を即座に表示。
    - **レポート表示**: テキストレポート + matplotlibレーダーチャートの左右分割表示。
    - **解析リセット**: 二重解析を回避しつつ、必要に応じて一からやり直す機能。

## セットアップ

### 依存関係
- Python 3.10+
- FFmpeg (Whisper/Demucs用)
- CUDA対応GPU推奨（CPU動作も可能）
## How to Use
### 1. 起動 (Startup)
フォルダ内の **`run_gui.bat`** をダブルクリックしてください。
Python環境がインストールされていれば、自動的に起動します。

### 2. 初回起動時の注意 (First Run)
初回のみ、以下のAIモデル（合計数GB）の自動ダウンロードが行われます。
**インターネット接続を確保し、完了までお待ちください。**
- Demucs (htdemucs_6s)
- Whisper (medium / large-v2)
- AudioSet (MIT/ast-finetuned)
- BS-Roformer

2回目以降は、オフラインで数秒で起動・解析が可能です。

### 3. 解析 (Analysis)
1. GUIでオーディオファイルを選択 ("Select Audio File...")。
2. 設定を調整し、"Run Analysis" をクリック。
    - **Instrumental Mode:** インスト曲の場合はチェックを入れると高速化されます。
    - **Open Output Folder:** 解析完了後、結果フォルダを直接開けます。
3. `output/` フォルダに結果が保存されます。

## Requirements
- Windows 10/11
- Python 3.10+
- CUDA-compatible GPU (Recommended for speed)
- `requirements.txt` を参照

```bash
pip install -r requirements.txt
```

### 起動

VSCode Tasks (`Ctrl+Shift+P` → `Tasks: Run Task`) または:

```bash
python gui.py
```

## プロジェクト構造
```text
.
├── gui.py                # アプリケーションのエントリポイント
├── modules/
│   ├── pipeline.py       # 各フェーズをオーケストレート
│   ├── surgeon.py        # 音源分離担当 (Demucs htdemucs_6s)
│   ├── demucs_runner.py  # torchaudio互換パッチ付きDemucsランナー
│   ├── analyst.py        # 音楽解析担当 (librosa + AudioSet + Whisper)
│   ├── profiler.py       # 汎用音声プロファイリング (16軸)
│   ├── exporter.py       # レポート・MIDI出力担当
│   ├── summarizer.py     # 解析結果の読み込みと要約
│   ├── archiver.py       # セッション・フォルダ管理
│   └── utils.py          # VRAM解放等のユーティリティ
├── docs/
│   └── future_roadmap.md # 将来の機能構想
├── output/               # 解析結果（ステム、JSON、レポート、MIDI）
└── requirements.txt      # 依存ライブラリ
```

## 解析結果の出力構造

各セッションの `analysis_report.json` には以下が含まれます:

| キー | 内容 |
|---|---|
| `vocals`, `drums`, `bass`, `guitar`, `piano`, `other` | 各ステムの解析データ |
| `structure` | 楽曲構成（サビ推定等） |
| `master_mix` | 2mix全体の AudioSet + 基本特徴量 |
| `voice_profile` | 16軸プロファイル + レーダーデータ + signature |
