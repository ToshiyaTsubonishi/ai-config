---
name: hr-system-admin-automation
description: "人事システム（COMPANY/HPM/CWS）のデータ登録、SharePointの権限管理、イントラネットのUI/コンテンツ更新、および情報セキュリティ設定を自動化し、システムの整合性を維持するスキル。"
version: 1.0.0
author: SBI Orchestrator
---
# hr-system-admin-automation (System Custodian)

## 1. Overview
人事業務の屋台骨となるシステムの健全性を守ります。
COMPANYへのマスター登録、SharePointの複雑なアクセス権限設定、およびイントラネットのタイムリーな更新を自動化。さらに、個人スマホからの安全なアクセス環境の整備や、電子化された規程類の適切な管理を行い、ガバナンスと利便性を両立させます。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| システムマスタ登録 | **Master Data Librarian** | 人事通達メール等から情報を読み取り、COMPANYやHPM等の各種システムへ正確にデータを反映させる。 |
| 権限・セキュリティ管理 | **Security Access Admin** | SharePointのフォルダ権限やスマホアクセスのセキュリティ設定を、依頼に基づき自動または半自動で実行・監査する。 |
| ポータル・リソース管理 | **Digital Asset Manager** | イントラネットのUI改善、規程類PDFのアーカイブ、およびシステムマニュアルの更新を統括する。 |

## 3. Workflow
1.  **Monitor**: `Master Data Librarian` が人事異動や制度変更の情報を常にキャッチアップ。
2.  **Execute**: 権限変更依頼を検知すると、`Security Access Admin` が承認状況を確認の上、即座に設定変更を実行。
3.  **Validate**: 登録されたデータの整合性チェックや、不要な旧データのクレンジング（SharePoint化）を定期実施。
4.  **Publish**: 新しいマニュアルや規程が完成次第、`Digital Asset Manager` がポータルを更新し、全社へ周知。

## 4. Available Resources
  - `references/document_retention_policy_2026.md`: 人事・労務書類 法定保存期間 & 廃棄ガイドライン。
  - `references/ai_governance_guideline.md`: HR Tech AI活用ガバナンス・倫理ガイドライン。
- **Assets**:
  - `assets/sharepoint_permission_matrix.md`: SharePoint 人事部権限管理マトリクス（2025年版）。

## 5. Operational Principles
*   **Zero Latency**: システム登録の遅延は手続きの滞留に直結するため、情報受領後速やかにアクションを開始する。
*   **Security by Design**: 権限付与は常に「最小限の原則」に基づき、定期的なアクセス権限の棚卸しを自動で支援する。
*   **User Empowerment**: ユーザーが迷わずシステムを利用できるよう、UIは簡潔に保ち、必要な情報を検索しやすい構造を維持する。
