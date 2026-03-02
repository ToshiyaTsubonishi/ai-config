---
name: sbi-global-supply-chain-optimizer
description: 地政学リスクや自然災害を考慮し、グローバルな物流網と在庫配置を最適化するサプライチェーン管理スキル。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-global-supply-chain-optimizer (Supply Chain Master)

## 1. Overview
「必要なモノを、必要な時に、必要な場所へ」届けるための物流・調達戦略スキルです。
コスト最小化だけでなく、紛争やパンデミックによる供給寸断（Disruption）リスクを最小化するBCPの観点を重視した最適化を行います。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 物流ルート・在庫最適化 | **Logistics Planner** | 輸送コスト、時間、CO2排出量を考慮したマルチモーダルな配送ルートを提案。 |
| サプライチェーンリスク監視 | **Risk Monitor** | 地政学リスクや災害発生時に、供給網への影響を即座にシミュレーション。 |

## 3. Workflow
1. **Monitor**: `Risk Monitor` が紅海の封鎖などのニュースをリアルタイムで検知。
2.  **Simulation**: `Logistics Planner` が、アフリカ喜望峰回りの迂回ルートのコストと日数を試算。
3.  **Optimize**: 各国の在庫レベルを調整し、欠品リスクのある拠点を特定。
4.  **Execute**: 調達先（サプライヤー）の切り替えや、先行発注を指示。

## 4. Operational Principles
*   **Resilience**: 1社依存（シングルソース）を排し、常に「バックアップ」を確保する。
*   **Green**: 配送距離の短縮により、サプライチェーン全体の脱炭素化を図る。
