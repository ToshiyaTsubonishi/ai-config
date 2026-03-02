---
name: sbi-investment-legal-orchestrator
description: 投資契約のドラフト作成、交渉、およびクロージングまでの法務プロセスを自動化・管理するリーガルテック・スキル。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-investment-legal-orchestrator (Deal Counsel)

## 1. Overview
VC/PE投資における法務プロセスをエンドツーエンドで支援するスキルです。
投資家と起業家の間の利益相反を調整し、スムーズな契約締結を支援します。タームシート（条件概要書）の内容を契約書（SPA/SHA）に自動反映させ、条項の抜け漏れや矛盾を防ぎます。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| クロージング実務 | **Deal Closing Bot** | CP充足確認、捺印、送金指示を一気通貫で管理。 |
| 契約書ドラフト作成 | **SPA Drafter** | タームシートに基づき、投資契約書・株主間契約書を自動生成。 |

## 3. Workflow
1. **Terms**: `Negotiation Strategist` が決定した条件を入力。
2.  **Draft**: `SPA Drafter` が契約書の初稿（First Draft）を作成。
3.  **Review**: 法務担当者が確認し、相手方と交渉。
4.  **Sign**: `Deal Closing Bot` が電子署名サービスへAPI送信。

## 4. Operational Principles
*   **Standardization**: SBIグループ標準の契約テンプレートを使用し、品質を均一化する。
*   **Version Control**: 契約書の版数管理を徹底し、先祖返りを防ぐ。
