---
name: fin-financial-planning
description: 予算策定、予実分析、およびローリングフォーキャストを通じて、企業の将来財務をデザインするスキル。
version: 2.0.0
author: SBI Orchestrator
---
# fin-financial-planning (FP&A)

## 1. Overview
「数字で未来を語る」ための財務計画スキルです。
過去の延長線上の予算ではなく、市場環境やKPIドライバーに基づいた動的な予測（Rolling Forecast）を行い、経営の意思決定を支援します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 予実差異分析 | **Budget Variance Analyst** | 単価差・数量差・為替差などを詳細に分解し、真の原因を特定。 |
| 着地見込み予測 | **Rolling Forecast Engine** | 最新の受注状況やトレンドを加味し、期末着地を自動更新。 |

## 3. Workflow
1. **Gather**: 各事業部からKPI（MAU, ARPU, 受注残）を収集。
2. **Predict**: `Rolling Forecast Engine` が、AIモデルを用いて売上・利益を予測。
3. **Analyze**: `Budget Variance Analyst` が予算との乖離を検出し、アクションプラン（コスト削減、販促強化）を提言。

## 4. Operational Principles
*   **Agility**: 年次予算に縛られず、四半期・月次での柔軟なリプランニングを推奨。
*   **Driver-Based**: 財務数値の裏にある「事業ドライバー」を重視する。
