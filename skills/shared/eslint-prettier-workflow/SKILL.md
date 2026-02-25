---
name: eslint-prettier-workflow
description: ESLint + Prettier の実行順序ルール、CI/ローカルでのコマンド固定、ESLint MCP との併用手順、自動修正の適用範囲ガイドライン。
---

# ESLint / Prettier ワークフロー

## 原則

- **ESLint**: コード品質（ルール違反の検出・修正）
- **Prettier**: コードフォーマット（整形のみ）
- 両者は **競合しない** ように設定する（`eslint-config-prettier` を使用）

## コマンド体系（固定）

```bash
# チェックのみ（CI 用）
pnpm lint          # = next lint && prettier --check .

# 自動修正（ローカル開発用）
pnpm lint:fix      # = next lint --fix && prettier --write .
```

> エージェントは **修正前に必ず `pnpm lint` でチェックのみを実行** し、問題を把握してから `lint:fix` を適用する。

## ESLint MCP との併用

ESLint MCP（`@eslint/mcp@latest`）が利用可能な場合:

1. MCP 経由で **現在のファイルの診断結果** を取得
2. エラーの内容を理解してからコード修正
3. 修正後に再度 MCP で診断を実行して解消を確認

MCP は **read-only の診断ツール** として使い、修正は CLI（`pnpm lint:fix`）で行う。

## 設定ファイル構成

```
project-root/
├── eslint.config.mjs     # ESLint Flat Config
├── .prettierrc            # Prettier 設定
├── .prettierignore        # Prettier 除外
└── .editorconfig          # エディタ共通設定
```

### eslint.config.mjs（最小構成）

```javascript
import { dirname } from 'path';
import { fileURLToPath } from 'url';
import { FlatCompat } from '@eslint/eslintrc';

const __dirname = dirname(fileURLToPath(import.meta.url));
const compat = new FlatCompat({ baseDirectory: __dirname });

export default [
  ...compat.extends('next/core-web-vitals', 'next/typescript'),
  ...compat.extends('prettier'), // Prettier との競合防止
];
```

### .prettierrc

```json
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100
}
```

## 自動修正の適用範囲

| 状況 | lint:fix 使用可否 | 理由 |
|------|------------------|------|
| 新規ファイル作成後 | ✅ 可 | 初期整形 |
| 既存ファイルの小修正 | ✅ 可 | 差分が明確 |
| 大規模リファクタ | ⚠️ 段階的に | diff が膨らみレビュー困難 |
| 他人のコードを含むファイル | ❌ 不可 | コミット履歴が汚れる |

## チェックリスト

- [ ] `eslint-config-prettier` が ESLint 設定に含まれているか
- [ ] `pnpm lint` が CI で実行されているか
- [ ] `pnpm lint:fix` がローカル開発で使用されているか
- [ ] ESLint MCP が接続されている場合、診断結果を確認してから修正しているか
- [ ] Prettier の設定が `.prettierrc` に明文化されているか
