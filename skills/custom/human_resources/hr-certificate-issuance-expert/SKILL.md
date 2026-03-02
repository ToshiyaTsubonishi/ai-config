---
name: hr-certificate-issuance-expert
description: "在籍証明書や年収証明書等の発行依頼をFormsで受け付け、人事システムからのデータ抽出、Wordテンプレートへの自動差し込み、発行・保管までを完結させるスキル。"
version: 1.0.0
author: SBI Orchestrator
---
# hr-certificate-issuance-expert (Certi-Forge)

## 1. Overview
煩雑な証明書発行業務を自動化します。
Formsで受け付けた依頼に対し、人事システム（COMPANYや社内システム）から必要な情報を自動抽出し、指定のWordテンプレートに正確に転記します。これにより、手書きや転記ミスを排除し、発行までのリードタイムを大幅に短縮します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| データ抽出・名寄せ | **HR Data Fetcher** | 人事システムやFormsの回答内容から、証明書に必要な項目（氏名、生年月日、年収、期間等）を正確に抽出する。 |
| 書類自動生成 | **Document Forge** | Wordテンプレートへの差し込み印刷機能を活用し、和文・英文を問わず高品質な証明書を生成する。 |
| 進捗・保管管理 | **Issuance Coordinator** | 承認フローの回覧、SharePointへの自動格納、発行完了通知の送付を管理する。 |

## 3. Workflow
1.  **Request**: Formsを通じて社員から発行依頼を受領。
2.  **Mapping**: `HR Data Fetcher` が人事システム内の最新データを取得し、依頼内容と照合。
3.  **Forge**: `Document Forge` が、役職や住所などの変動項目をテンプレートに流し込み、PDF/Wordを作成。
4.  **Complete**: 担当者の最終確認後、`Issuance Coordinator` が保存先（SharePoint）へ移動し、申請者へ完了連絡。

## 4. Available Resources
  - `references/word_template_technical_spec.md`: Wordテンプレートの技術的仕様・レイアウト崩れ対策。
- **Assets**:
  - `assets/document_mapping_definition.md`: 証明書発行Formsとシステム項目のマッピング定義。
- **References**:
  - `references/certificate_issuance_sop.md`: 証明書発行業務の標準操作手順書。

## 5. Operational Principles
*   **Zero Mistake**: 公的な証明書であるため、氏名や数値の1文字の誤りも許さない厳格なデータ検証を行う。
*   **Format Flexibility**: 自治体や提出先によって異なる特殊なフォーマット要求にも対応できるよう、テンプレートの切り替えを柔軟に行う。
*   **Security**: 個人情報の漏洩を防ぐため、作業中の一時ファイルは処理完了後に即座に破棄し、SharePointの権限管理を徹底する。
