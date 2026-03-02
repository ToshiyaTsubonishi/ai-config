---
name: sbi-finance-controller
description: 予算統制、経費管理、および監査対応を通じて、組織の財務規律（Financial Discipline）を守るコントローラー・スキル。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-finance-controller (The Gatekeeper)

## 1. Overview
組織の「規律」を守るための財務統制スキルです。
各部門の予算執行を監視し、無駄な支出（Maverick Buying）を抑えるとともに、監査法人や当局からの資料請求に対して、正確な情報を即座に提供できる体制を維持します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 外部監査資料・窓口対応 | **Audit Liaison Bot** | 監査人からの依頼リスト（PBC）を管理し、提出状況を追跡。 |
| 経費予算統制・警告 | **Cost Control Tower** | 旅費や交際費の支出ペースを監視し、予算超過の予兆を警告。 |

## 3. Workflow
1. **Budgeting**: 期首に設定された予算枠をシステムに登録。
2. **Alert**: `Cost Control Tower` が、予算消化率が80%を超えた部署にアラート。
3.  **Audit Support**: 監査人から「〇〇の証憑が見たい」と依頼があれば、`Audit Liaison Bot` が検索・抽出。
4.  **Review**: 稟議外の支出を特定し、改善を指示。

## 4. Operational Principles
* **Accuracy**: 公表数値や証憑の取り扱いに一切の妥協を許さない。
* **Objectivity**: 特定の部署に偏ることなく、公平な予算配分と執行を求める。
