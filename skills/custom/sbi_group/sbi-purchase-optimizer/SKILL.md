---
name: sbi-purchase-optimizer
description: グループ全体の購買データを分析し、ボリュームディスカウントや共同調達によってコストを削減するスキル。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-purchase-optimizer (Group Sourcing)

## 1. Overview
SBIグループ全体の購買力を集約し、コストリーダーシップを確立するスキルです。
各社がバラバラに行っている購買（サーバー、SaaS、備品など）を名寄せし、大口契約による割引や、サプライヤーリスクの集中管理を行います。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 支出分析・名寄せ | **Spend Analyzer** | 勘定科目から不適切な個別調達（Maverick Buying）を発見。 |
| サプライヤーリスク管理 | **Vendor Risk Manager** | 取引先の経営状況やESG対応状況を定期監査。 |

## 3. Workflow
1. **Aggregate**: グループ各社のERPから購買データを自動収集。
2.  **Compare**: 同一製品の購入単価の差を特定。
3.  **Negotiate**: `supplier-negotiator` 連携により、グループ統合契約への切り替えを交渉。
4.  **Monitor**: `Vendor Risk Manager` が、サプライヤーの倒産リスクや不祥事を監視。

## 4. Operational Principles
* **Cost Efficiency**: 単なる安値追求ではなく、TCO（総保有コスト）の最小化を目指す。
* **Compliance**: 取引先の選定において、透明性と公平性を担保する。
