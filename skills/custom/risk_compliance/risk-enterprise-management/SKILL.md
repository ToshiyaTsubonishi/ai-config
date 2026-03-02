---
name: risk-enterprise-management
description: 信用リスク、市場リスク、オペレーショナルリスクを統合的に管理し、全社的なリスク許容度（Risk Appetite）の範囲内で事業を推進するERMスキル。
version: 2.0.0
author: SBI Orchestrator
---
# risk-enterprise-management (CRO Office)

## 1. Overview
「リスクを取らなければリターンはない」が、「取ってはいけないリスク」は徹底的に排除するスキルです。
グループ全体のリスク量を定量化（VaR）し、経営体力（自己資本）の範囲内に収まっているかを監視します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 統合リスクモニタリング | **CRO Dashboard Agent** | 全種類のリスクをダッシュボード化し、経営層にアラートを出す。 |
| モデルリスク管理（MRM） | **Model Risk Auditor** | AIや数理モデルの判断ミスによる損失を防ぐ。 |

## 3. Workflow
1. **Aggregate**: 各事業部から信用リスク、市場リスク、オペリスクのデータを収集。
2.  **Calculate**: 相関を考慮して統合リスク量（Integrated VaR）を計算。
3.  **Audit**: `Model Risk Auditor` が、計算に使われたモデルの前提条件が正しいか検証。

## 4. Operational Principles
*   **Risk Culture**: 「悪い情報ほど早く報告する」文化をシステムで支える。
*   **Stress Test**: 過去の危機（リーマンショック等）のシナリオで耐久力をテストする。
