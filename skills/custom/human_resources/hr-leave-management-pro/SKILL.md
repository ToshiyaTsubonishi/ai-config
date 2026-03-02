---
name: hr-leave-management-pro
description: "産育休や傷病休職の管理をデジタル化し、AIによる制度解説や過去事例の検索、外部ツール連携を通じて休職者・担当者双方の不安を解消するスキル。"
version: 1.0.0
author: SBI Orchestrator
---
# hr-leave-management-pro (Leave Concierge)

## 1. Overview
産育休や傷病休職に関わる煩雑な管理業務を統合します。
「アドバンテッジ社 ハーモニー」等の外部ツールとの連携や、AIによる「産育休コンシェルジュ」機能を提供し、過去事例の調査や書類の期日管理、手続きのペーパーレス化を推進します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 個別休職ケース管理 | **Leave Case Manager** | 個別ボックス形式で、申請状況、連絡履歴、提出書類を統合管理する。 |
| 制度・事例QA対応 | **Leave AI Concierge** | 就業規則、制度、過去事例、FAQを基に、休職者や担当者の質問に回答し、メールの下書きを生成する。 |
| 外部ツール・WF連携 | **Leave System Bridge** | アドバンテッジ社ツールや社内ワークフローとのデータ同期、ペーパーレス申請の実行。 |

## 3. Workflow
1.  **Ingest**: `Leave Case Manager` が、新規休職発生時に個別の管理スレッドを作成し、期日（産前産後、育休開始等）をセット。
2.  **Support**: 休職者からの質問に対し、`Leave AI Concierge` が社内規定に基づき即座に回答。
3.  **Operation**: 必要な書類送付や連絡を `Leave Case Manager` がリマインド。
4.  **Sync**: 承認された情報は `Leave System Bridge` を介して人事システムや外部管理ツールへ自動反映。

## 4. Available Resources
  - `references/bpo_collaboration_protocol.md`: 人事BPO・外部社労士 (SATO便) 連携標準フロー。
  - `assets/return_to_work_interview_sheet.md`: 復職支援 統合面談シート (メンタル・産育休共通)。
- **Assets**:
  - `assets/leave_management_milestone.md`: 産育休・介護休の手続きマイルストーン。
- **References**:
  - `references/leave_law_revision_2025.md`: 2025年改正育児・介護休業法の実務対応ガイド。

## 5. Operational Principles
*   **Empathy**: 休職者は不安を抱えていることが多いため、AIの回答やメール文面は温かみのある表現を心がける。
*   **Accuracy**: 制度解釈の誤りはトラブルに直結するため、不確実な場合は必ず「最終判断は担当者へ」と添える。
*   **History Tracking**: 担当者が交代しても経緯が即座に把握できるよう、全てのやり取りと判断根拠を構造化して記録する。
