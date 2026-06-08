# 114514coin Tracker 🚀

> 次世代の電子ゴミ（草コイン）を、日本円（JPY）でリアルタイム追跡。

`114514coin Tracker` は、価値の変動が激しい「114514coin」をはじめとする暗号資産を、日本円建てでスマートにモニタリングするためのWebアプリケーション・サーバープログラムです。

## 💎 特徴

-   **JPY リアルタイム換算**: 暗号資産の価格を瞬時に日本円に変換。
-   **直感的なチャート**: `lightweight-charts` を採用し、滑らかな価格推移を表示。
-   **モダンなスタック**: Next.js 16 (App Router) + TypeScript による高速で堅牢な動作。
-   **PWA 対応**: モバイル端末でもネイティブアプリのような体験。
-   **ダークモード完備**: 深夜のトレードでも目に優しい `next-themes` 統合。

## 🛠 テクノロジースタック

-   **Frontend**: [Next.js 16](https://nextjs.org/), [React 19](https://reactjs.org/)
-   **Styling**: [Tailwind CSS](https://tailwindcss.com/), [Shadcn UI](https://ui.shadcn.com/)
-   **State Management**: [Zustand](https://github.com/pmndrs/zustand)
-   **Charts**: [Lightweight Charts](https://www.tradingview.com/lightweight-charts/)
-   **Infrastructure**: Docker, Cloud Run 対応

## 🚀 クイックスタート

### 開発環境の起動

```bash
npm install
npm run dev
```

### ビルドとデプロイ

```bash
npm run build
npm start
```

## 🐳 Docker 構成

Dockerfile が同梱されているため、以下のコマンドでコンテナ化が可能です。

```bash
docker build -t 114514coin-tracker .
docker run -p 3000:3000 114514coin-tracker
```

## 📄 ライセンス

MIT License.
