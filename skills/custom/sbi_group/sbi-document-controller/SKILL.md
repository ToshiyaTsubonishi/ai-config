---
name: sbi-document-controller
description: 契約書、稟議書、会議資料などの重要文書をデジタル化し、バージョン管理とアクセス制御を徹底する文書管理スキル。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-document-controller (Document Keeper)

## 1. Overview
「探す時間」をゼロにし、「捨てるべきもの」を自動で捨てるスキルです。
紙文化からの完全脱却を目指し、電子署名、版数管理、そして法定保存期間に基づくライフサイクル管理を徹底します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 文書保存・廃棄管理 | **Retention Policy Enforcer** | 法令（会社法、税法）に基づいて保存期間を設定し、期限切れ文書を自動廃棄。 |
| 押印・電子署名フロー | **Seal Compliance Bot** | 権限規定に基づいた承認フローを回し、電子印鑑を付与。 |

## 3. Workflow
1. **Upload**: 文書をクラウドストレージに保存。
2.  **Classify**: 文書の種類（契約書、請求書）を自動判別し、タグ付け。
3.  **Sign**: `Seal Compliance Bot` が承認者に通知し、署名を取得。
4.  **Archive**: `Retention Policy Enforcer` が「7年後」に廃棄フラグを立てる。

## 4. Operational Principles
*   **Searchability**: 全文検索（OCR）を可能にし、過去のナレッジを再利用しやすくする。
*   **Access Control**: 機密レベルに応じた閲覧制限をかける。
