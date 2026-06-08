# Future Roadmap & Feature Proposals

> ✅ = 実装済み, 🔧 = 部分実装, 📋 = 未実装

## ✅ 5. 汎用音声プロファイリング (Voice Profiling)
- **状態**: 実装済み (`modules/profiler.py`)
- **概要**: 解析データを統合し、インスト8軸+ボーカル8軸のプロファイルを自動生成。
- **実装内容**:
  - 辞書ベースの軸定義（後から追加・修正可能）
  - `combined_signature`: LLMがキャラ名/アーティスト名を想起できるレベルの詳細テキスト
  - GUIにmatplotlibレーダーチャート表示
  - ASCIIバーチャートによるテキストレポート内可視化

## ✅ 6. マスター音源の全体解析 (Mix-wide Analysis)
- **状態**: 実装済み (`analyst.py` → `analyze_master_mix`)
- **概要**: Stem分離前の2mix音源全体に AudioSet + librosa を適用。
- **結果**: テンポ/キー/LUFS/リズムパターン/全体ジャンル感をレポートに表示。

---

## 📋 1. AI評論家 (The AI Critic)
- **概要**: ロールプレイを行うLLM (Gemma 2, Llama 3等) を統合し、解析データに基づいた「辛口レビュー」や「感情豊かな感想」を生成する。
- **機能**:
  - ユーザーとの対話機能
  - 楽曲の改善点提案
  - 歌詞の内容に基づいた深読み解説

## 📋 2. 自動リミックス・マスタリング (Auto-Remix/Mastering)
- **概要**: 解析されたEQバランスやダイナミクス情報を元に、FFmpegやSoXを用いてオーディオを自動加工する。
- **機能**:
  - "Bass Boost" 版の自動生成
  - "Vocal Remove" (Karaoke) 版の自動書き出し
  - 特定の帯域をカットして楽器練習用トラックを作成

## 📋 3. 自動MV生成 (Auto-MV Generator)
- **概要**: ビートトラッキング情報と楽曲の展開（Aメロ/サビ）に合わせて、画像生成AIやエフェクトを同期させた動画を生成する。
- **機能**:
  - `MoviePy` を使用した動画編集の自動化
  - 歌詞の字幕生成 (Whisperのタイムスタンプ活用)

## 📋 4. 高度なMIDI編集 (Advanced MIDI)
- **概要**: 生成されたMIDIをさらに人間らしく（Humanize）調整する。
- **機能**:
  - ベロシティのランダム化
  - グリッドからの微細なズレ（Groove）の再現

## 📋 7. ローカルLLMによる統合解釈 (Local LLM Integration)
- **概要**: 解析された全JSONデータをローカルLLM (Gemma 2, Llama 3等) にプロンプトとして渡し、より人間的で文脈の深い音楽評論を生成させる。
- **利点**: ルールベースの `summarizer` では不可能な、「この時代の空気感」や「歌詞の行間を読む」解説が可能になる。

## ✅ 8. ステム分離精度の改善 (Separation Quality)
- **状態**: 実装済み (`modules/surgeon.py`, `modules/roformer_runner.py`)
- **概要**: BS-Roformer (SDR ~13dB) + Demucs のハイブリッド分離。反復ブレンドオプション付き。
- **モード**:
  - `Standard`: 従来のDemucs 6s（高速）
  - `Hybrid`: BS-Roformer(Vocal) + Demucs(Instruments) — ボーカル品質大幅向上
  - `Iterative Blending`: Hybridモード時にα-ブレンド反復で更なる精度向上 (2-4パス)

## ✅ 9. GUI機能強化 (GUI Enhancements)
- **状態**: 実装済み (`gui.py`)
- **概要**: ユーザー体験向上のためのインターフェース改善。
- **機能**:
  - **分離設定パネル**: `Standard` / `Hybrid` モードの切り替えと反復回数の調整。
  - **非同期処理**: 重い解析処理を別スレッドで実行し、UIのフリーズを回避。
  - **リッチなレポート表示**: 左側にテキスト、右側にレーダーチャートを配置した見やすいビューア。

