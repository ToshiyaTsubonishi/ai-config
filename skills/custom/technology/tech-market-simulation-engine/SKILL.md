---
name: tech-market-simulation-engine
description: 株式市場や経済圏をマルチエージェント・シミュレーションで再現し、ショックイベントや規制変更の影響を予測するスキル。
version: 1.0.0
author: Gemini Skill Creator
---
# tech-market-simulation-engine (Market Twin)

## 1. Overview
**What is this?**
数百万の投資家エージェント（機関投資家、個人、HFTアルゴリズム）が相互作用する仮想市場を構築するスキルです。
過去のデータの延長線上で予測するのではなく、「もし全員がこう動いたら」という創発的な現象（暴落、バブル）をシミュレーションします。

**When to use this?**
*   新しい取引所システムの負荷テスト（注文集中時の挙動確認）を行う場合。
*   金融危機（リーマンショック級）が発生した際の、自社ポートフォリオへの影響を測る場合。
*   新しい金融規制が市場流動性に与えるインパクトを事前評価する場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| クラッシュ・ストレステスト | **Crash Simulator** | `../../agents/crash-simulator.md` |
| 市場再現・エージェント生成 | **Market Digital Twin** | `../../agents/market-digital-twin.md` |

### 2.2 Workflow
1.  **Build**: `Market Digital Twin` が、実際の市場参加者の属性に近いエージェント群を生成。
2.  **Shock**: `Crash Simulator` が「原油価格の急騰」などの外部ショックを与える。
3.  **Observe**: エージェントたちの売り注文が連鎖し、価格が暴落する過程を観察。

## 3. Bundled Resources
*   No specific assets listed.

## 4. Safety
*   **Model Risk**: シミュレーション結果は現実と異なる可能性があることを明記する。