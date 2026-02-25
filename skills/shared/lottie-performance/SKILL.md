---
name: lottie-performance
description: Lottie アニメーションのパフォーマンスバジェット。Canvas/WebGL レンダリング強制、SVG レンダリング禁止、非アクティブ時の停止ルール。ストリーミング動画との共存を保証する。
---

# Lottie パフォーマンスバジェット

## 原則

Lottie アニメーションは動画プレイヤーとの共存環境で使用されるため、**再生パフォーマンスへの影響を最小限に抑える** ことが絶対条件。

## 不変条件

### 1. レンダリング方式

| 方式 | 判定 | 理由 |
|------|------|------|
| Canvas | ✅ 推奨 | DOM ノード数に影響なし、GPU 描画 |
| WebGL (lottie-web) | ✅ 許可 | Canvas より高速な場合あり |
| SVG | ❌ **禁止** | DOM ノード膨張、リフロー発生、動画再生に干渉 |

```tsx
// ✅ 正しい: Canvas レンダラー指定
import lottie from 'lottie-web';

lottie.loadAnimation({
  container: elementRef.current,
  renderer: 'canvas', // ← 必須
  loop: true,
  autoplay: false,
  animationData: overlayAnimation,
});
```

```tsx
// ❌ 禁止: SVG レンダラー（デフォルト値）
lottie.loadAnimation({
  container: elementRef.current,
  // renderer 未指定 → SVG がデフォルト → 禁止
  animationData: overlayAnimation,
});
```

### 2. 非アクティブ時の完全停止

オーバーレイが非表示のとき、Lottie アニメーションの再生を **完全に停止** する。

```typescript
// オーバーレイ表示制御
function useOverlayLottie(isVisible: boolean) {
  const animRef = useRef<AnimationItem | null>(null);

  useEffect(() => {
    if (!animRef.current) return;

    if (isVisible) {
      animRef.current.play();
    } else {
      animRef.current.stop(); // pause ではなく stop（フレーム位置リセット）
    }
  }, [isVisible]);

  return animRef;
}
```

### 3. JSON サイズ制限

| 指標 | 上限 | 根拠 |
|------|------|------|
| JSON ファイルサイズ | **100KB 以下**（gzip前） | モバイル回線での初期ロード |
| レイヤー数 | **20 以下** | Canvas レンダリング負荷 |
| フレームレート | **30fps** | 動画プレイヤー（通常30fps）と同期 |
| 同時再生数 | **1** | CPU/GPUリソース競合防止 |

### 4. 遅延ロード

Lottie JSON は初期バンドルに含めず、**必要時に動的インポート** する。

```typescript
// ✅ 動的インポート
const loadOverlayAnimation = async () => {
  const { default: data } = await import('../assets/overlay-anim.json');
  return data;
};
```

## 検証手順

```bash
# JSON サイズチェック
wc -c src/assets/*.json | awk '$1 > 102400 { print "⚠️ OVER 100KB:", $2 }'

# レイヤー数チェック
node -e "
  const fs = require('fs');
  const data = JSON.parse(fs.readFileSync(process.argv[1]));
  console.log('Layers:', data.layers?.length ?? 0);
  if ((data.layers?.length ?? 0) > 20) console.error('⚠️ Too many layers');
" src/assets/overlay-anim.json
```

## チェックリスト

- [ ] `renderer: 'canvas'` が明示されているか
- [ ] 非表示時に `stop()` が呼ばれているか（`pause()` ではなく）
- [ ] JSON サイズが 100KB 以下か
- [ ] レイヤー数が 20 以下か
- [ ] 動的インポートで遅延ロードされているか
- [ ] 動画プレイヤーとの同時表示でフレームドロップが発生しないか
