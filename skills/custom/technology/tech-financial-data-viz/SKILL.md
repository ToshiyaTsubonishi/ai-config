---
name: tech-financial-data-viz
description: 複雑な金融データを、トレーダーや経営者が直感的に理解できるチャートやダッシュボードに変換する可視化スキル。
version: 1.0.0
author: Gemini Skill Creator
---
# tech-financial-data-viz (Visual Alpha)

## 1. Overview
**What is this?**
株価、為替、板情報（Order Book）、ポートフォリオのリスク指標などの数値の羅列を、意味のある「情報」として可視化するスキルです。
D3.jsやWebGLを駆使し、ミリ秒単位で更新されるリアルタイム・チャートを描画します。

**When to use this?**
*   HFT（高頻度取引）の約定状況をヒートマップで表示する場合。
*   ポートフォリオのリスク分散状況をサンキー図で可視化する場合。
*   経営ダッシュボードに、リアルタイムのKPIを表示する場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| チャート生成・可視化コード作成 | **Chart Wizard Agent** | `../../agents/chart-wizard-agent.md` |
| リアルタイム・ダッシュボード構築 | **Real-Time Dashboarder** | `../../agents/real-time-dashboarder.md` |

### 2.2 Workflow
1.  **Stream**: WebSocketなどでリアルタイムデータを受信。
2.  **Process**: `Real-Time Dashboarder` がデータを集計・加工（ダウンサンプリング等）。
3.  **Render**: `Chart Wizard Agent` が最適なチャート形式を選択し、描画コード（React Component）を生成。

## 3. Bundled Resources
*   `scripts/example_script.py`: データ生成スクリプト例

## 4. Safety
*   **Performance**: 大量データの描画でブラウザをクラッシュさせないよう、GPUアクセラレーションを活用する。