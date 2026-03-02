---
name: tech-insurtech-engineering
description: IoTデータを用いた保険商品の開発、引受（アンダーライティング）、および保険金支払いを自動化するインシュアテック・スキル。
version: 1.0.0
author: Gemini Skill Creator
---
# tech-insurtech-engineering (Parametric Insurance)

## 1. Overview
**What is this?**
「雨が降ったら即座に支払う」ようなパラメトリック保険や、テレマティクス（運転挙動）連動型保険を技術的に実装するスキルです。
オラクル（外部データ）との連携と、スマートコントラクトによる自動執行が核となります。

**When to use this?**
*   航空機遅延保険をブロックチェーン上で構築する場合。
*   ドライブレコーダーのデータから事故リスクを算定し、保険料を割り引く場合。
*   保険金請求（Claims）プロセスをチャットボットで自動化する場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| IoTリスク評価・保険料算定 | **IoT Risk Underwriter** | `../../agents/iot-risk-underwriter.md` |
| パラメトリック支払い実行 | **Parametric Payout Bot** | `../../agents/parametric-payout-bot.md` |

### 2.2 Workflow
1.  **Sense**: IoTデバイスや気象APIからデータを取得。
2.  **Assess**: `IoT Risk Underwriter` がリスクスコアを更新。
3.  **Trigger**: 閾値（例: 震度5以上）を超えたら、`Parametric Payout Bot` が自動で送金処理を実行。

## 3. Bundled Resources
*   `scripts/example_script.py`: リスク計算スクリプト例

## 4. Safety
*   **Oracle Failure**: 外部データの取得失敗に備え、複数のデータソースを参照する。