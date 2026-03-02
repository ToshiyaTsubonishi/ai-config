---
name: proc-strategic-sourcing
description: 購買データの分析に基づき、サプライヤー選定、価格交渉、および契約管理を最適化する戦略調達スキル。
version: 2.0.0
author: SBI Orchestrator
---
# proc-strategic-sourcing (Cost Cutter)

## 1. Overview
「購買」を単なる事務作業から「利益を生み出す戦略」へと変えるスキルです。
支出分析（Spend Analysis）でコスト削減の機会を見つけ、論理的な価格交渉で有利な条件を引き出します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| RFP作成・評価 | **RFP Generator** | ベンダーに求める要件を明確化し、公正な競争入札を実施。 |
| 価格交渉・条件最適化 | **Supplier Negotiator** | 市場相場や他社の見積もりを武器に、タフな交渉を行う。 |

## 3. Workflow
1. **Analyze**: 過去の購買データを分析し、「どのカテゴリでコストが上がっているか」を特定。
2.  **Request**: `RFP Generator` が、複数のベンダーに提案を依頼。
3.  **Negotiate**: `Supplier Negotiator` が、価格だけでなく納期や品質を含めたトータルコストで交渉。

## 4. Operational Principles
*   **TCO**: 購入価格だけでなく、維持費や廃棄費を含めた総保有コスト（TCO）で判断する。
*   **Partnership**: サプライヤーを「叩く」のではなく、共に改善するパートナーとして扱う。
