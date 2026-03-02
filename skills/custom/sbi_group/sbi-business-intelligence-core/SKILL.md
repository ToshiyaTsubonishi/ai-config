---
name: sbi-business-intelligence-core
description: 経営判断に必要な全データ（財務、市場、競合、社内KPI）に加え、未来予測（Simulation）とセキュリティリスク（Red Teaming）を統合・可視化する「SBIグループの全能の眼」。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-business-intelligence-core (Group Cockpit)

## 1. Overview
SBIグループの経営層（Board members）向けの意思決定支援スキルです。
過去の「実績データ」だけでなく、SNSやニュースから得られる「感情データ」、そしてAIによる「予測データ」を統合し、全方位的な視界を提供します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 財務指標分析・予実監視 | **Financial Insight Generator** | ROIC、自己資本比率等の重要指標をリアルタイムで算出。 |
| 市場感情・レピュテーション | **Market Sentiment Tracker** | 風評被害の予兆や、新サービスへの市場の反応を検知。 |
| 戦略シナリオ・予測 | **Strategic Scenario Simulator** | 「もし金利が1%上がったら？」といった問いに数秒で回答。 |

## 3. Workflow
1. **Gather**: `market-data-miner` 連携により、社内外のデータを収集。
2. **Synthesize**: `Financial Insight Generator` が財務インパクトを試算。
3. **Trace**: `Market Sentiment Tracker` が、顧客や株主の期待値を分析。
4. **Predict**: `Strategic Scenario Simulator` が、最適な経営資源の配分案を提示。

## 4. Operational Principles
* **Single Source of Truth**: 誰が見ても同じ数字に基づく、透明性の高い分析。
* **Forward-looking**: 過去の反省ではなく、未来の打ち手を議論するためのデータを提供する。
