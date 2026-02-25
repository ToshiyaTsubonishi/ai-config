# AGENTS.md — フロントエンド開発プロジェクト テンプレート

> **使い方**: このファイルをプロジェクトルートにコピーし、`AGENTS.md` にリネームして使う。
> `<!-- CUSTOMIZE -->` のセクションはプロジェクトに合わせて編集する。

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| UI ライブラリ | React 19 |
| フレームワーク | Next.js (App Router) |
| 言語 | TypeScript (strict mode) |
| テスト（ユニット） | node:test |
| テスト（E2E） | Playwright |
| リンター | ESLint (Flat Config) |
| フォーマッター | Prettier |
| アニメーション | GSAP + @gsap/react |

## 標準コマンド

エージェントは以下のコマンドのみを使用する。未定義のコマンドを推測で実行してはならない。

```bash
pnpm dev          # 開発サーバー起動
pnpm build        # プロダクションビルド
pnpm lint         # ESLint + Prettier チェック（修正なし）
pnpm lint:fix     # ESLint + Prettier 自動修正
pnpm test         # node:test 全テスト実行
pnpm test:watch   # node:test ウォッチモード
pnpm e2e          # Playwright E2E テスト
pnpm typecheck    # tsc --noEmit 型検証
```

## 実装→検証ループ

エージェントが実装変更を行った後は、以下の順序で必ず検証する:

1. `pnpm typecheck` — 型エラーの検出
2. `pnpm lint` — 静的解析
3. `pnpm test` — ユニットテスト
4. `pnpm e2e` — E2E（影響範囲に応じて）

## 参照すべき Skills

| スキル名 | 用途 |
|---------|------|
| `react-gsap-rules` | React × GSAP の結合ルール（useGSAP 強制） |
| `animation-adapter` | アニメーション抽象化層の I/F と制約 |
| `lottie-performance` | Lottie パフォーマンスバジェット |
| `realtime-event-testing` | WebSocket/SSE のモック・テスト手法 |
| `playwright-visual-verification` | 視覚的隠蔽の自動テスト |
| `node-test-runner` | node:test の実行ルール |
| `eslint-prettier-workflow` | ESLint/Prettier ワークフロー |
| `nextjs-scaffold` | Next.js プロジェクト初期化手順 |

## ディレクトリ構成

```
src/
├── app/                  # Next.js App Router
├── components/
│   ├── ui/               # 汎用 UI コンポーネント
│   └── features/         # 機能特化コンポーネント
├── hooks/                # カスタムフック
├── lib/
│   ├── event-adapter.ts  # リアルタイム通信アダプタ
│   └── animation/        # アニメーション抽象化層
├── styles/               # CSS
├── types/                # TypeScript 型定義
└── __tests__/
    ├── unit/             # ユニットテスト
    ├── integration/      # 統合テスト
    └── fixtures/         # テストデータ
```

## コーディング規約

1. GSAP は **必ず `useGSAP` フック経由** で実行する（`useEffect` 内での直接実行は禁止）
2. アニメーションは **Animation Adapter 経由** で呼び出す（GSAP 直接 import を避ける）
3. `prefers-reduced-motion` 対応は Adapter 層で一元管理する
4. コンポーネントのテストは `data-testid` 属性を使用する
5. 型定義は `src/types/` に集約する

## セキュリティ

- API キー・トークン・秘密鍵を出力・コミットしない
- 環境変数は `.env.local`（gitignore 対象）に格納

<!-- CUSTOMIZE: ドメイン固有のルール -->
## プロジェクト固有の不変条件

<!-- 以下はオークション配信プロジェクトの例。プロジェクトに合わせて書き換える。 -->

### オーバーレイ制御
- `SECRET_LOT` イベント受信時、動画プレイヤーを **完全に隠蔽** する
- 隠蔽の判定基準: z-index > player、opacity = 1、Bounding Box が player を完全カバー
- 詳細は `playwright-visual-verification` スキルを参照

### リアルタイムイベント
- バックエンドからのシグナルは `EventEmitter` パターンで抽象化する
- テストでは MSW / スタブを使い、実サーバーに依存しない
- 詳細は `realtime-event-testing` スキルを参照

### Lottie アニメーション
- レンダラーは `canvas` 固定（SVG 禁止）
- 非表示時はアニメーションを `stop()` で完全停止
- 詳細は `lottie-performance` スキルを参照
<!-- /CUSTOMIZE -->
