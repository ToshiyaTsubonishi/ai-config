---
name: sales-planner
description: Generates region-specific sales strategies and target lists for corporate financial products. Use when needing detailed sales execution plans for specific Japanese prefectures.
version: 2.0.0
author: SBI Orchestrator
---
# sales-planner (Regional Tactics)

## 1. Overview
地域ごとの経済特性（産業構造、県民性）を考慮した、泥臭い営業戦略を立案するスキルです。
「島根県では製造業へのアプローチが有効」「福岡県では観光業が狙い目」といった地域特化の戦術を授けます。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 地域データ分析 | **Region Specific Miner** | 帝国データバンク等の情報から、成長企業を抽出。 |
| 営業リスト作成 | **Regional Sales Strategist** | ドアノック商材（最初に提案すべき商品）を選定し、アタックリストを作成。 |

## 3. Workflow
1. **Analyze**: `Region Specific Miner` が地域のニュースや求人情報を分析。
2.  **Target**: 「売上が伸びている建設業」などの条件でターゲットを抽出。
3.  **Plan**: `Regional Sales Strategist` が、訪問ルートを最適化。

## 4. Operational Principles
*   **Locality**: 地域の言葉や話題を盛り込み、親近感を醸成する。
*   **Efficiency**: 移動時間を最小化し、商談時間を最大化する。