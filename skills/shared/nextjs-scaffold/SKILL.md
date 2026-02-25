---
name: nextjs-scaffold
description: Next.js プロジェクトの初期セットアップ手順。create-next-app の選択肢固定（App Router / TypeScript / ESLint）、ディレクトリ規約、npm scripts 標準化。
---

# Next.js プロジェクトセットアップ

## 初期化コマンド

```bash
npx create-next-app@latest ./ \
  --typescript \
  --eslint \
  --app \
  --src-dir \
  --import-alias "@/*" \
  --use-pnpm \
  --no-tailwind \
  --no-turbopack
```

> `--no-tailwind`: CSS 方式はプロジェクトごとに決定する。
> `--no-turbopack`: 安定性を優先。必要に応じて後から有効化する。

## ディレクトリ規約

```
src/
├── app/                  # Next.js App Router
│   ├── layout.tsx
│   ├── page.tsx
│   └── (routes)/
├── components/           # 再利用可能な UI コンポーネント
│   ├── ui/               # 汎用 UI（Button, Modal 等）
│   └── features/         # 機能特化コンポーネント
├── hooks/                # カスタムフック
├── lib/                  # ユーティリティ・ヘルパー
│   ├── event-adapter.ts  # リアルタイム通信アダプタ
│   └── animation/        # アニメーション抽象化層
├── styles/               # グローバル CSS / CSS Modules
├── types/                # TypeScript 型定義
└── __tests__/            # node:test テストファイル
```

## npm scripts 標準化

以下を `package.json` に定義し、エージェントのコマンド入口を統一する。

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint && prettier --check .",
    "lint:fix": "next lint --fix && prettier --write .",
    "test": "node --test src/__tests__/**/*.test.ts",
    "test:watch": "node --test --watch src/__tests__/**/*.test.ts",
    "e2e": "playwright test",
    "e2e:ui": "playwright test --ui",
    "typecheck": "tsc --noEmit"
  }
}
```

## 初期化後の追加セットアップ

1. ESLint 設定拡張（`eslint.config.mjs`）
2. Prettier 設定（`.prettierrc`）
3. Playwright 設定（`playwright.config.ts`）
4. GSAP + `@gsap/react` インストール
5. `AGENTS.md`（または `AGENTS.frontend.md` テンプレート）をルートに配置

## チェックリスト

- [ ] `src/` ディレクトリ構成になっているか
- [ ] App Router（`src/app/`）を使用しているか
- [ ] 上記 npm scripts がすべて定義されているか
- [ ] TypeScript strict mode が有効か（`tsconfig.json`）
- [ ] `.gitignore` に `.next/`, `node_modules/`, `.env.local` が含まれているか
