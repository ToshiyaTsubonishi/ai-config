---
name: tech-generative-content-engine
description: AIによる視覚・言語的クリエイティブの大量生成と、データに基づくパーソナライゼーションを実現するマーケティング・テクノロジースキル。
version: 1.0.0
author: Gemini Skill Creator
---
# tech-generative-content-engine (Creative AI)

## 1. Overview
**What is this?**
Stable Diffusion, Midjourney, GPT-4 などの生成AIモデルをパイプライン化し、高品質なマーケティング素材（バナー、LP、動画、コピー）を自動生成するスキルです。
単に作るだけでなく、A/Bテストの結果をフィードバックし、最も効果の高いクリエイティブを学習・量産します。

**When to use this?**
*   広告キャンペーン用のバナー画像を大量に生成する場合。
*   ユーザーの属性や行動に合わせて、Webサイトのキャッチコピーを出し分ける場合。
*   ブランドイメージに合った、オリジナルの画像素材を作成する場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| 広告コピー・テキスト生成 | **Copy Ad Optimizer** | `../../agents/copy-ad-optimizer.md` |
| 画像・動画アセット生成 | **Creative Asset Generator** | `../../agents/creative-asset-generator.md` |

### 2.2 Workflow
1.  **Input**: キャンペーンの目的、ターゲット層、ブランドガイドラインを入力。
2.  **Generate**: `Creative Asset Generator` が数十パターンの画像を作成。`Copy Ad Optimizer` がコピー案を生成。
3.  **Optimize**: 過去のCTRデータに基づき、最適な組み合わせを選定。
4.  **Deploy**: 広告配信プラットフォーム（`neo-media-ad-ops`連携）に入稿。

## 3. Bundled Resources
*   No specific assets listed.

## 4. Safety
*   **Copyright**: 生成されたコンテンツが他者の著作権を侵害していないか、常にチェックする。
*   **Brand Safety**: ブランド毀損につながる不適切な表現（差別、暴力など）をフィルタリングする。