---
name: tech-neuro-finance
description: 脳科学（Neuroscience）と金融を融合させ、トレーダーの直感やバイアスを数値化・最適化する実験的スキル。
version: 1.0.0
author: Gemini Skill Creator
---
# tech-neuro-finance (Brain Trading)

## 1. Overview
**What is this?**
トレーダーの脳波（EEG）や皮膚電位などの生体信号を解析し、集中力やストレス状態を可視化するスキルです。
「ゾーン」に入っている時の脳波パターンを特定し、パフォーマンス向上やリスク回避（感情的な損切りの防止）に役立てます。

**When to use this?**
*   プロップトレーダーのメンタル管理を行う場合。
*   市場全体の「恐怖指数」を、実際の投資家の生体データから推測する場合。
*   脳波で注文を出すBCI（Brain-Computer Interface）の実験を行う場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| 脳波・生体データ処理 | **BCI Data Handler** | `../../agents/bci-data-handler.md` |
| 感情・アルファ生成 | **Emotion Alpha Trader** | `../../agents/emotion-alpha-trader.md` |

### 2.2 Workflow
1.  **Measure**: ヘッドセットから脳波データを取得。
2.  **Analyze**: `BCI Data Handler` がノイズを除去し、集中度（Beta波）やリラックス度（Alpha波）を算出。
3.  **Feedback**: `Emotion Alpha Trader` が「焦っています。深呼吸してください」とアラート。

## 3. Bundled Resources
*   No specific assets listed.

## 4. Safety
*   **Privacy**: 脳波データは究極のプライバシー（思考）に関わるため、本人の同意なしに保存・分析しない。