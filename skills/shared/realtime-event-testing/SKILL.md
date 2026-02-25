---
name: realtime-event-testing
description: リアルタイム通信（WebSocket/SSE）のモック・テスト手法。MSW によるエミュレーション、node:test 内での EventEmitter スタブ化、オークション進行シグナルのシミュレーション。
---

# リアルタイムイベントのモックとテスト

## 原則

リアルタイムなシグナル（WebSocket, SSE）をトリガーとするUIロジックは、**実サーバーなしでシミュレーション可能** な環境を常に維持する。

## アーキテクチャ

```
[実サーバー / MSW Mock]
        ↓ WebSocket / SSE
[接続層: EventEmitter Adapter]
        ↓ 標準化イベント
[UI ロジック: 状態管理 / 表示制御]
```

接続層は `EventEmitter` パターンで抽象化し、テスト時にスタブへ差し替え可能にする。

## 接続アダプタの実装例

```typescript
// lib/event-adapter.ts
import { EventEmitter } from 'events';

export interface AuctionEvent {
  type: 'LOT_CHANGE' | 'BID_UPDATE' | 'SECRET_LOT' | 'OVERLAY_ON' | 'OVERLAY_OFF';
  payload: Record<string, unknown>;
  timestamp: number;
}

export class AuctionEventAdapter extends EventEmitter {
  connect(url: string): void { /* WebSocket接続の実装 */ }
  disconnect(): void { /* クリーンアップ */ }
}
```

## node:test でのスタブ化

```typescript
import { describe, it, mock } from 'node:test';
import assert from 'node:assert/strict';
import { AuctionEventAdapter, type AuctionEvent } from '../lib/event-adapter.js';

describe('オーバーレイ制御', () => {
  it('SECRET_LOT イベントでオーバーレイが表示される', () => {
    const adapter = new AuctionEventAdapter();

    // スタブ: 実サーバーなしでイベント発火
    const event: AuctionEvent = {
      type: 'SECRET_LOT',
      payload: { lotId: 'LOT-042' },
      timestamp: Date.now(),
    };

    let overlayVisible = false;
    adapter.on('SECRET_LOT', () => { overlayVisible = true; });
    adapter.emit('SECRET_LOT', event);

    assert.equal(overlayVisible, true);
  });

  it('OVERLAY_OFF イベントでオーバーレイが非表示になる', () => {
    const adapter = new AuctionEventAdapter();
    let overlayVisible = true;

    adapter.on('OVERLAY_OFF', () => { overlayVisible = false; });
    adapter.emit('OVERLAY_OFF', { type: 'OVERLAY_OFF', payload: {}, timestamp: Date.now() });

    assert.equal(overlayVisible, false);
  });
});
```

## MSW によるWebSocketモック（ブラウザ/統合テスト用）

```typescript
// mocks/handlers.ts
import { ws } from 'msw';

const auction = ws.link('wss://api.example.com/auction');

export const handlers = [
  auction.addEventListener('connection', ({ client }) => {
    // 接続直後のステータス送信
    client.send(JSON.stringify({
      type: 'LOT_CHANGE',
      payload: { lotId: 'LOT-001', status: 'active' },
      timestamp: Date.now(),
    }));
  }),
];
```

## テストシナリオの標準化

| シナリオ | 発火イベント | 期待結果 |
|---------|------------|---------|
| 通常表示 → 秘密ロット | `SECRET_LOT` | オーバーレイ表示 |
| 秘密ロット → 通常復帰 | `OVERLAY_OFF` | オーバーレイ非表示 |
| 接続断 → 再接続 | `disconnect` → `connect` | 最新状態に復帰 |
| 高速連続イベント | 100ms間隔で `LOT_CHANGE` x5 | 最後のイベントのみ反映 |

## チェックリスト

- [ ] 接続アダプタが `EventEmitter` で抽象化されているか
- [ ] テストで実サーバーに依存していないか
- [ ] MSW ハンドラが `mocks/` 配下に配置されているか
- [ ] 再接続・エラーリカバリのテストが含まれているか
- [ ] イベントの型定義が共有されているか
