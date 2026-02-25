---
name: node-test-runner
description: Node.js 標準テストランナー（node:test）の実行ルール。コマンド固定、フィルタリング、カバレッジ、テストファイル配置規約、AI ループでの回帰実行パターン。
---

# node:test 実行ルール

## 原則

テストランナーは Node.js 標準の `node:test` を使用する。Jest/Vitest/Mocha は導入しない。

## 実行コマンド（固定）

```bash
# 全テスト実行
node --test src/__tests__/**/*.test.ts

# 名前フィルタ
node --test --test-name-pattern="オーバーレイ" src/__tests__/**/*.test.ts

# カバレッジ付き実行
node --test --experimental-test-coverage src/__tests__/**/*.test.ts

# 監視モード（開発時）
node --test --watch src/__tests__/**/*.test.ts
```

> **注意**: TypeScript 実行には `--loader tsx` や `tsx` ラッパーが必要な場合がある。
> プロジェクトの `package.json` の `test` スクリプトを正とする。

## テストファイル配置

```
src/__tests__/
├── unit/                    # 純粋関数・ロジックのテスト
│   ├── overlay-logic.test.ts
│   └── event-adapter.test.ts
├── integration/             # コンポーネント統合テスト
│   └── auction-flow.test.ts
└── fixtures/                # テストデータ
    ├── mock-events.json
    └── sample-config.json
```

## テストの書き方

```typescript
import { describe, it, before, after, mock } from 'node:test';
import assert from 'node:assert/strict';

describe('オーバーレイ判定ロジック', () => {
  it('SECRET_LOT ステータスで true を返す', () => {
    const result = shouldShowOverlay({ type: 'SECRET_LOT' });
    assert.equal(result, true);
  });

  it('通常ステータスで false を返す', () => {
    const result = shouldShowOverlay({ type: 'LOT_CHANGE' });
    assert.equal(result, false);
  });
});
```

## AI ループでの回帰テスト

エージェントが実装変更後に実行すべきコマンド:

```bash
# 1. 型検証
npx tsc --noEmit

# 2. ユニットテスト
node --test src/__tests__/unit/

# 3. 統合テスト（影響範囲に応じて）
node --test src/__tests__/integration/

# 4. ESLint（MCP 経由でも可）
npx next lint
```

この順序を守ることで、早い段階で問題を検出できる。

## チェックリスト

- [ ] `package.json` の `test` スクリプトが `node --test` を使用しているか
- [ ] テストファイルが `src/__tests__/` 配下にあるか
- [ ] `node:test` の `describe`/`it`/`assert` を使っているか（Jest 互換 API ではなく）
- [ ] モック関数は `node:test` の `mock` を使用しているか
- [ ] カバレッジは `--experimental-test-coverage` で取得しているか
