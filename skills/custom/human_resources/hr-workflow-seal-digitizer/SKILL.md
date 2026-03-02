---
name: hr-workflow-seal-digitizer
description: "会議のペーパーレス化、社内申請の電子承認、および紙書類のOCRによるデジタル転記を推進し、物理的な制約を排除した効率的なワークフローを構築するスキル。"
version: 1.0.0
author: SBI Orchestrator
---
# hr-workflow-seal-digitizer (Streamline Master)

## 1. Overview
「紙」と「ハンコ」を人事部から一掃します。
会議資料のデジタル配信、ワークフローシステムを活用した電子押印、および残ってしまった紙書類のAI-OCRによる自動データ化を推進。場所を選ばない働き方を支援し、物理的な保管コストや紛失リスク、回覧の待ち時間を劇的に削減します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| ペーパーレス会議支援 | **Paperless Meeting Bot** | 資料のデジタル一括配付、閲覧権限の自動管理、およびノートPC持参の推奨通知を行う。 |
| 電子押印・WF構築 | **Workflow Architect** | 紙の申請書をデジタルフォーム化し、電子印影を用いた多段階承認フローを設計・実行する。 |
| 紙書類データ化 (OCR) | **Document Digitizer** | 郵送等で届いた紙書類をスキャンデータから解析し、人事システムやExcelへ自動転記する。 |

## 3. Workflow
1.  **Preparation**: `Paperless Meeting Bot` が会議前に資料をSharePointへ集約し、参加者へリンクを共有。
2.  **Conversion**: 既存の紙申請書を `Workflow Architect` がデジタル化し、各ステップの承認者を自動設定。
3.  **Operation**: 申請が上がると、承認者へリマインドを送信。進捗の滞留を可視化。
4.  **Ingest**: どうしても発生する外部からの紙書類は `Document Digitizer` が読み取り、後続の業務へ繋ぐ。

## 4. Available Resources
  - `references/ocr_optimization_guide.md`: AI-OCR 精度向上・帳票設計ガイドライン。
- **References**:
  - `references/digital_submission_guide_2025.md`: 2025年1月 電子申請義務化対応ガイドライン。

## 5. Operational Principles
*   **Security First**: デジタル化に伴い、閲覧権限の設定を厳格に行い、個人情報や重要会議資料の漏洩を防止する。
*   **User Friction Reduction**: 従来の紙の運用に慣れたユーザーでもスムーズに移行できるよう、直感的なUIと操作ガイドを提供する。
*   **Process Transparency**: 「誰のところで止まっているか」を常に可視化し、業務の停滞を未然に防ぐ。
