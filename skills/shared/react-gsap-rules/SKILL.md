---
name: react-gsap-rules
description: React × GSAP の厳格な結合ルール。useGSAP フック強制、メモリリーク・重複実行の防止、Context Safe パターン。React Strict Mode 耐性を保証する。
---

# React × GSAP 結合ルール

## 原則

React 環境（特に Strict Mode）で GSAP を使用する場合、**必ず `@gsap/react` の `useGSAP` フックを使用すること**。

`useEffect` 内での直接的な GSAP アニメーション実行は **禁止** とする。

## 禁止パターン

```tsx
// ❌ 禁止: useEffect 内で直接 GSAP を実行
useEffect(() => {
  gsap.to('.box', { x: 100 });
  // クリーンアップ漏れ → メモリリーク
  // Strict Mode で2重実行 → アニメーション重複
}, []);
```

## 必須パターン

```tsx
import { useGSAP } from '@gsap/react';
import gsap from 'gsap';

function AnimatedBox() {
  const containerRef = useRef<HTMLDivElement>(null);

  // ✅ 必須: useGSAP フックのスコープ内で実行
  useGSAP(() => {
    gsap.to('.box', { x: 100, duration: 1 });
  }, { scope: containerRef });

  return (
    <div ref={containerRef}>
      <div className="box" />
    </div>
  );
}
```

## Context Safe メソッド呼び出し

イベントハンドラなど `useGSAP` のコールバック外でアニメーションを実行する場合は、`contextSafe` を使用する。

```tsx
function ClickableBox() {
  const containerRef = useRef<HTMLDivElement>(null);

  const { contextSafe } = useGSAP({ scope: containerRef });

  // ✅ contextSafe でラップしたハンドラ
  const handleClick = contextSafe(() => {
    gsap.to('.box', { rotation: '+=360', duration: 1 });
  });

  return (
    <div ref={containerRef}>
      <div className="box" onClick={handleClick} />
    </div>
  );
}
```

## タイムラインの管理と破棄

複雑なアニメーションシーケンスでは `gsap.timeline()` を使い、コンポーネントアンマウント時に自動で kill される設計にする。

```tsx
function SequenceAnimation() {
  const containerRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    const tl = gsap.timeline();
    tl.to('.step1', { opacity: 1, duration: 0.5 })
      .to('.step2', { x: 100, duration: 0.5 })
      .to('.step3', { scale: 1.2, duration: 0.3 });
    // useGSAP がアンマウント時に自動で tl.kill() を実行
  }, { scope: containerRef });

  return (
    <div ref={containerRef}>
      <div className="step1" />
      <div className="step2" />
      <div className="step3" />
    </div>
  );
}
```

## チェックリスト

- [ ] `@gsap/react` がインストールされているか
- [ ] GSAP の `registerPlugin` は App のエントリポイントで1回だけ実行しているか
- [ ] すべてのアニメーションが `useGSAP` のスコープ内で動作しているか
- [ ] イベントハンドラのアニメーションは `contextSafe` でラップされているか
- [ ] `scope` に適切な `ref` が渡されているか（DOM セレクタの衝突防止）
- [ ] React Strict Mode（開発環境）で重複実行がないか確認済みか
