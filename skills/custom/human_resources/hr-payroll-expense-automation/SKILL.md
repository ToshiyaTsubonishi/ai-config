---
name: hr-payroll-expense-automation
description: "給与計算、年末調整、出向按分、および請求書精算業務をデジタル化し、手作業によるミスを排除しつつ、ペーパーレスな支払いフローを実現するスキル。"
version: 1.0.0
author: SBI Orchestrator
---
# hr-payroll-expense-automation (Wealth Guard)

## 1. Overview
「人」に関わる金流のデジタル完結を目指します。
年末調整の完全ペーパーレス化、出向按分表の自動作成、および経費BANKと連携した電子承認フローの構築により、毎月の支払処理や年次イベントの工数を大幅に削減。税務・会計上の正確性を担保しながら、迅速な決済を実現します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 年調・給与DX支援 | **Tax Adjustment Assistant** | 年末調整の進捗管理、書類の不備チェック、およびCOMPANY等の給与システムへのデータ連携を支援する。 |
| 請求書・按分処理 | **Settlement Processor** | 出向按分表の自動計算、BtoBプラットフォームへの請求書発行、および小口精算の電子承認を代行する。 |
| 整合性チェック | **Audit & Compliance Bot** | 振込データとエビデンスの突合、および関連法規への準拠状況を自動で検証する。 |

## 3. Workflow
1.  **Ingest**: `Settlement Processor` が外部プラットフォームや経費BANKからデータを受信。
2.  **Calculate**: 出向按分などの複雑なロジックをAIが実行し、最新の人事情報メールの内容を反映した按分表を作成。
3.  **Approve**: 承認待ちタスクを関係者へリマインド。電子押印・電子承認フローで完結。
4.  **Finalize**: `Tax Adjustment Assistant` が、年末調整や給与改定の情報をシステムへ一括流し込み、処理完了。

## 4. Available Resources
  - `assets/secondment_apportionment_schema.md`: 出向費用按分・較差補填金 管理表定義。
  - `references/apportionment_logic_spec.md`: 出向費用 按分計算ロジック・税務処理定義。
- **Assets**:
  - `assets/year-end_adjustment_checklist_2025.md`: 2025年版 年末調整実務チェックリスト。

## 5. Operational Principles
*   **Zero Defect**: 金銭を扱う業務であるため、全ての計算結果に対してダブルチェック（AIによる自己検証と担当者確認）を義務付ける。
*   **Timeliness**: 支払期日の厳守は絶対であり、ボトルネックとなっている承認ステップを早期に特定・通知する。
*   **Security & Privacy**: 給与データ等の極めて機密性の高い情報は、アクセス制限を徹底し、匿名化が必要な場合は適切に処理する。
