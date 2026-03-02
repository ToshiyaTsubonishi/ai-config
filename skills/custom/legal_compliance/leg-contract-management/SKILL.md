---
name: leg-contract-management
description: 契約書の作成から締結、更新、保管までのライフサイクル全体（CLM）を管理するスキル。
version: 2.0.0
author: SBI Orchestrator
---
# leg-contract-management (Smart CLM)

## 1. Overview
契約書を「紙」ではなく「データ」として管理するスキルです。
締結後の管理（更新期限のアラート、権利義務の履行）を自動化し、契約に埋め込まれたビジネス価値を最大化します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 契約ライフサイクル管理 | **Lifecycle Manager** | 契約のステータス（交渉中、締結済、更新時期）を一元管理。 |
| リカード契約（コード化） | **Ricardian Coder** | 契約条項をコードに変換し、条件が満たされたら自動実行。 |

## 3. Workflow
1. **Store**: 締結された契約書をデータベースに格納し、検索可能にする。
2.  **Extract**: `Legal Entity Extractor`（`tech-legal-ai-engineering` 傘下）が重要項目（終了日、違約金）を抽出。
3.  **Alert**: `Lifecycle Manager` が、解約予告期限の前に担当者へ通知。
4.  **Execute**: `Ricardian Coder` が、スマートコントラクトを通じて支払いを実行。

## 4. Operational Principles
*   **Searchability**: 過去の契約書を「条項単位」で検索できるようにする。
*   **Automation**: 人間が忘れがちな期限管理をシステムで担保する。
