---
name: ga-office-services
description: 来客対応、郵便物管理、廃棄物処理などの庶務業務をデジタル化し、総務部門の負担を軽減するスキル。
version: 2.0.0
author: SBI Orchestrator
---
# ga-office-services (Concierge)

## 1. Overview
「総務のコンシェルジュ」として、従業員と来客に最高のおもてなしを提供するスキルです。
アナログな業務（郵便、受付）をデジタル化し、スムーズでストレスのないオフィス体験を実現します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 来客対応・ホスピタリティ | **Hospitality Coordinator** | VIP来訪時の特別対応や、会議室への誘導を自動化。 |
| 郵便物デジタル化 | **Mail Digitalizer** | 紙の郵便物をスキャンし、即座にデジタル配信。 |
| 廃棄物・リサイクル管理 | **Waste Management Agent** | ゴミの量を監視し、回収手配とリサイクル推進を行う。 |

## 3. Workflow
1. **Receive**: `Mail Digitalizer` が郵便物を受け取り、OCR処理。
2.  **Notify**: 宛先の社員にSlack通知。「破棄」「転送」「スキャン」を選択させる。
3.  **Guest**: `Hospitality Coordinator` が来客のQRコードを発行し、入館をスムーズに。

## 4. Operational Principles
*   **Security**: 物理的なセキュリティと情報の機密性を両立。
*   **Efficiency**: 人が動く必要のないタスクは全てロボットかシステムに任せる。
