---
name: playwright-visual-verification
description: Playwright による「視覚的隠蔽」の自動テスト。Bounding Box 重なり計算、Visual Regression Testing（VRT）、z-index・透明度を含む隠蔽完全性検証。
---

# Playwright による視覚的隠蔽の検証

## 原則

「映像が隠れていること」の判定は、DOM 上の要素存在だけでは不十分。**z-index の重なり順序、透明度、Bounding Box の物理的カバー範囲** を含めた多層検証を行う。

## 検証レベル

| レベル | 手法 | 検出できる問題 |
|--------|------|-------------|
| L1: DOM 存在確認 | `locator.isVisible()` | 要素の表示/非表示 |
| L2: Bounding Box 重なり | 座標計算 | z-index ミス、サイズ不足 |
| L3: CSS プロパティ検証 | `evaluate` | 透明度、pointer-events |
| L4: Visual Regression | スクリーンショット比較 | ピクセル単位の漏れ |

## L1: DOM 存在確認

```typescript
import { test, expect } from '@playwright/test';

test('オーバーレイ要素がSECRET_LOTイベントで表示される', async ({ page }) => {
  await page.goto('/auction');

  // イベント発火をシミュレート
  await page.evaluate(() => {
    window.dispatchEvent(new CustomEvent('auction:secret-lot', {
      detail: { lotId: 'LOT-042' },
    }));
  });

  const overlay = page.locator('[data-testid="video-overlay"]');
  await expect(overlay).toBeVisible();
});
```

## L2: Bounding Box 重なり検証

```typescript
test('オーバーレイが動画プレイヤーを完全にカバーしている', async ({ page }) => {
  await page.goto('/auction');
  await triggerSecretLot(page);

  const playerBox = await page.locator('[data-testid="video-player"]').boundingBox();
  const overlayBox = await page.locator('[data-testid="video-overlay"]').boundingBox();

  expect(playerBox).not.toBeNull();
  expect(overlayBox).not.toBeNull();

  // オーバーレイがプレイヤーを完全にカバーしているか
  expect(overlayBox!.x).toBeLessThanOrEqual(playerBox!.x);
  expect(overlayBox!.y).toBeLessThanOrEqual(playerBox!.y);
  expect(overlayBox!.x + overlayBox!.width).toBeGreaterThanOrEqual(
    playerBox!.x + playerBox!.width
  );
  expect(overlayBox!.y + overlayBox!.height).toBeGreaterThanOrEqual(
    playerBox!.y + playerBox!.height
  );
});
```

## L3: CSS プロパティ検証

```typescript
test('オーバーレイの z-index が動画プレイヤーより高い', async ({ page }) => {
  await page.goto('/auction');
  await triggerSecretLot(page);

  const zIndexes = await page.evaluate(() => {
    const player = document.querySelector('[data-testid="video-player"]');
    const overlay = document.querySelector('[data-testid="video-overlay"]');
    return {
      player: parseInt(getComputedStyle(player!).zIndex) || 0,
      overlay: parseInt(getComputedStyle(overlay!).zIndex) || 0,
      overlayOpacity: parseFloat(getComputedStyle(overlay!).opacity),
      overlayPointerEvents: getComputedStyle(overlay!).pointerEvents,
    };
  });

  expect(zIndexes.overlay).toBeGreaterThan(zIndexes.player);
  expect(zIndexes.overlayOpacity).toBe(1); // 透明度が1（完全不透明）
});
```

## L4: Visual Regression Testing（VRT）

```typescript
test('SECRET_LOT 時のスクリーンショットが参照画像と一致', async ({ page }) => {
  await page.goto('/auction');
  await triggerSecretLot(page);

  // 動画プレイヤー領域のスクリーンショットを撮影
  const playerArea = page.locator('[data-testid="video-player-container"]');

  await expect(playerArea).toHaveScreenshot('overlay-active.png', {
    maxDiffPixelRatio: 0.01, // 1%以下の差分を許容
    animations: 'disabled',  // CSS アニメーションを停止して安定化
  });
});

test('通常時のスクリーンショット（オーバーレイなし）', async ({ page }) => {
  await page.goto('/auction');

  const playerArea = page.locator('[data-testid="video-player-container"]');

  await expect(playerArea).toHaveScreenshot('overlay-inactive.png', {
    maxDiffPixelRatio: 0.01,
    animations: 'disabled',
  });
});
```

## ヘルパー関数

```typescript
// tests/helpers/auction.ts
import type { Page } from '@playwright/test';

export async function triggerSecretLot(page: Page) {
  await page.evaluate(() => {
    window.dispatchEvent(new CustomEvent('auction:secret-lot', {
      detail: { lotId: 'LOT-042' },
    }));
  });
  // オーバーレイ表示アニメーション完了を待機
  await page.waitForSelector('[data-testid="video-overlay"][data-visible="true"]');
}

export async function triggerOverlayOff(page: Page) {
  await page.evaluate(() => {
    window.dispatchEvent(new CustomEvent('auction:overlay-off'));
  });
  await page.waitForSelector('[data-testid="video-overlay"][data-visible="false"]');
}
```

## チェックリスト

- [ ] `data-testid` が動画プレイヤーとオーバーレイの両方に設定されているか
- [ ] L2（Bounding Box）テストが CI に含まれているか
- [ ] VRT の参照画像（スナップショット）がリポジトリに管理されているか
- [ ] アニメーション中のスクリーンショットが `animations: 'disabled'` で安定化されているか
- [ ] 複数ビューポートサイズ（desktop/tablet/mobile）でのテストがあるか
