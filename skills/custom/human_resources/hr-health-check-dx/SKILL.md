---
name: hr-health-check-dx
description: "二次健診の自動案内および健診費用の請求書チェックを自動化し、実施率向上と担当者の負担軽減を実現するスキル。"
version: 1.0.0
author: SBI Orchestrator
---
# hr-health-check-dx (Health Vigilante)

## 1. Overview
従業員の健康管理において重要な「二次健診」の受診勧奨と、外部機関からの請求書突合作業をDX化します。
案内の埋もれや未開封を防ぐ自動リマインド、および目視で行っていた請求書の内容確認を自動化することで、業務の正確性とスピードを向上させます。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 二次健診の案内・リマインド | **HealthCheck AutoMailer** | 対象者リストに基づき、パーソナライズされた案内メールとForms未回答者への自動追撃を行う。 |
| 請求書内容の突合・検証 | **Invoice Audit Agent** | 健診機関からの請求書データと社内管理表を比較し、人数・単価・項目に差異がないか検証する。 |

## 3. Workflow
1.  **Extraction**: `Invoice Audit Agent` が、健診費用の請求書（PDF/CSV）から「利用人数」「単価」「項目」を抽出。
2.  **Audit**: 社内管理表のデータと突合し、不一致があればアラートを発報。経費BANKへの入力用フォーマットで出力。
3.  **Targeting**: `HealthCheck AutoMailer` が、健診結果データから二次健診対象者を特定。
4.  **Action**: テンプレートに基づき、対象者へ案内を送信。Formsの回答状況を定期監視し、未回答者へ自動リマインド。

## 4. Available Resources
- **Assets**:
  - `assets/reminder_email_template.md`: 二次健診受診勧奨の標準メール。
- **References**:
  - `references/health_check_compliance_guide.md`: 労災二次健診制度の法的要件・判定基準。

## 5. Operational Principles
*   **Privacy First**: 健康診断結果は機微情報であるため、必要最小限のデータのみを処理し、ログ保存には細心の注意を払う。
*   **Consistency**: 担当者が変わっても品質が維持されるよう、抽出ロジックやメール文面は標準化されたテンプレートを使用する。
*   **Clarity**: リマインドメールは「1分で完了」など、相手の負担感（心理的ハードル）を下げる文言を採用する。
