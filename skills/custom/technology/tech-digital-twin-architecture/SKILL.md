---
name: tech-digital-twin-architecture
description: 物理空間（都市、工場、オフィス）の情報をデジタル空間に再現し、シミュレーションと最適化を行うデジタルツイン基盤スキル。
version: 1.0.0
author: Gemini Skill Creator
---
# tech-digital-twin-architecture (Mirror World)

## 1. Overview
**What is this?**
IoTセンサー、LiDAR、BIMデータを統合し、リアルタイムで変化する「デジタルの双子」を構築するスキルです。
都市開発のシミュレーションや、災害時の避難ルート策定、工場のライン最適化などに活用します。

**When to use this?**
*   スマートシティの交通流やエネルギー消費を可視化したい場合。
*   「震度6の地震が起きたら？」といった災害シミュレーションを行う場合。
*   オフィスの人流データを分析し、レイアウトを変更する場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| シミュレーション実行 | **Scenario Sim Agent** | `../../agents/scenario-sim-agent.md` |
| 空間データ統合・3D化 | **Spatial Data Aggregator** | `../../agents/spatial-data-aggregator.md` |

### 2.2 Workflow
1.  **Sense**: 街中のカメラやセンサーからデータを収集。
2.  **Map**: `Spatial Data Aggregator` が3D地図上にデータをマッピング。
3.  **Simulate**: `Scenario Sim Agent` が人流や気象の変化をシミュレーション。
4.  **Feedback**: 最適な信号制御や空調設定を、物理世界の機器にフィードバック。

## 3. Bundled Resources
*   No specific assets listed.

## 4. Safety
*   **Latency**: 物理世界へのフィードバックは、通信遅延による事故を防ぐため、エッジコンピューティングを活用する。