---
name: animation-adapter
description: アニメーション抽象化層のインターフェース定義。fadeIn/fadeOut/slideIn 等の標準 API、prefers-reduced-motion 対応、パフォーマンスバジェット（60fps）、GSAP ↔ 他ライブラリ差し替え互換規約。
---

# アニメーション抽象化層（Animation Adapter）

## 原則

アニメーション実装は **GSAP に直接依存するコードを最小化** し、抽象化層（Adapter）を介して呼び出す。これにより:

- GSAP ↔ Web Animations API ↔ CSS Transitions の差し替えが可能
- `prefers-reduced-motion` への一元対応
- パフォーマンスバジェットの強制

## インターフェース定義

```typescript
// lib/animation/types.ts

export interface AnimationOptions {
  duration?: number;       // 秒単位（デフォルト: 0.3）
  delay?: number;          // 秒単位（デフォルト: 0）
  ease?: string;           // イージング名（デフォルト: 'power2.out'）
  onComplete?: () => void;
}

export interface AnimationAdapter {
  fadeIn(element: HTMLElement, options?: AnimationOptions): void;
  fadeOut(element: HTMLElement, options?: AnimationOptions): void;
  slideIn(element: HTMLElement, direction: 'left' | 'right' | 'top' | 'bottom', options?: AnimationOptions): void;
  slideOut(element: HTMLElement, direction: 'left' | 'right' | 'top' | 'bottom', options?: AnimationOptions): void;
  scale(element: HTMLElement, from: number, to: number, options?: AnimationOptions): void;
  kill(element: HTMLElement): void;  // 進行中アニメーションの即時停止
  killAll(): void;                   // 全アニメーションの即時停止
}
```

## GSAP 実装

```typescript
// lib/animation/gsap-adapter.ts
import gsap from 'gsap';
import type { AnimationAdapter, AnimationOptions } from './types';

const REDUCED_MOTION = typeof window !== 'undefined'
  && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

function resolveOptions(opts?: AnimationOptions) {
  if (REDUCED_MOTION) {
    return { duration: 0, delay: 0, ease: 'none', onComplete: opts?.onComplete };
  }
  return {
    duration: opts?.duration ?? 0.3,
    delay: opts?.delay ?? 0,
    ease: opts?.ease ?? 'power2.out',
    onComplete: opts?.onComplete,
  };
}

export const gsapAdapter: AnimationAdapter = {
  fadeIn(el, opts) {
    const o = resolveOptions(opts);
    gsap.fromTo(el, { opacity: 0 }, { opacity: 1, ...o });
  },
  fadeOut(el, opts) {
    const o = resolveOptions(opts);
    gsap.to(el, { opacity: 0, ...o });
  },
  slideIn(el, dir, opts) {
    const o = resolveOptions(opts);
    const axis = dir === 'left' || dir === 'right' ? 'x' : 'y';
    const value = dir === 'left' || dir === 'top' ? -100 : 100;
    gsap.fromTo(el, { [axis]: value, opacity: 0 }, { [axis]: 0, opacity: 1, ...o });
  },
  slideOut(el, dir, opts) {
    const o = resolveOptions(opts);
    const axis = dir === 'left' || dir === 'right' ? 'x' : 'y';
    const value = dir === 'left' || dir === 'top' ? -100 : 100;
    gsap.to(el, { [axis]: value, opacity: 0, ...o });
  },
  scale(el, from, to, opts) {
    const o = resolveOptions(opts);
    gsap.fromTo(el, { scale: from }, { scale: to, ...o });
  },
  kill(el) {
    gsap.killTweensOf(el);
  },
  killAll() {
    gsap.globalTimeline.clear();
  },
};
```

## prefers-reduced-motion 対応（必須）

- `REDUCED_MOTION` が `true` の場合、**すべてのアニメーションを `duration: 0` で即時完了** させる。
- アニメーションを「非表示にする」のではなく「即座に最終状態にする」。
- これを **個別コンポーネントではなく Adapter 層で一元管理** する。

## パフォーマンスバジェット

| 指標 | 基準値 | 計測方法 |
|------|--------|---------|
| フレームレート | **60fps 維持** | Chrome DevTools > Performance |
| 同時アニメーション数 | **5 以下** | Adapter 内カウンタ |
| transform 制限 | `transform` + `opacity` のみ | レイアウト再計算を回避 |
| will-change | 必要時のみ付与、完了後に除去 | メモリ消費抑制 |

### 禁止プロパティ（アニメーション対象として）

```
❌ width, height         → transform: scale() を使用
❌ top, left, right      → transform: translate() を使用
❌ margin, padding       → レイアウトシフト発生
❌ border-radius の大変化 → ペイント負荷
```

## テスト指針

```typescript
import { describe, it, mock } from 'node:test';
import assert from 'node:assert/strict';

describe('AnimationAdapter', () => {
  it('reduced motion 時は duration が 0 になる', () => {
    // window.matchMedia をモック
    const adapter = createAdapterWithReducedMotion(true);
    // fadeIn の duration が 0 であることを検証
  });

  it('kill() で進行中のアニメーションが停止する', () => {
    // kill 後に要素の状態が最終値になっていることを検証
  });
});
```

## チェックリスト

- [ ] UI コンポーネントが GSAP を直接 import していないか（Adapter 経由か）
- [ ] `prefers-reduced-motion` が Adapter 層で処理されているか
- [ ] アニメーション対象が `transform` と `opacity` に限定されているか
- [ ] `will-change` が不要時に除去されているか
- [ ] 同時アニメーション数が 5 以下に制御されているか
