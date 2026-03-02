---
name: hr-contract-lifecycle-manager
description: "雇用契約、出向契約、人材紹介契約等の作成・締結をデジタル化し、AIによる契約条項の自動抽出や電子署名ツールとの連携により、事務負担とコストを削減するスキル。"
version: 1.0.0
author: SBI Orchestrator
---
# hr-contract-lifecycle-manager (Contract Navigator)

## 1. Overview
契約業務のフルデジタル化を実現します。
Wordで作成された契約書からの重要項目（氏名、発令日、条件等）のAI抽出、クラウドサイン等の電子契約システムとの連携、および契約条件のエビデンス管理を統合。紙の印刷・郵送コストをゼロにし、契約締結までのスピードを最大化します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 契約項目AI抽出 | **Contract Analyzer AI** | Word/PDF契約書を読み込み、氏名、期間、給与等の必要項目を自動でExcel/SharePoint形式にリスト化する。 |
| 電子締結プロセス管理 | **Signature Orchestrator** | クラウドサイン等へのアップロード、署名状況のトラッキング、完了後の自動アーカイブを実行する。 |
| デジタルエビデンス管理 | **Compliance Archiver** | 契約条件の根拠（メール、承認記録等）をデータ上で紐付け、監査に耐えうる状態で保管する。 |

## 3. Workflow
1.  **Extract**: `Contract Analyzer AI` がドラフト契約書から重要項目を抽出し、管理リストを作成。
2.  **Verify**: 担当者が抽出結果を確認。不一致や表記の揺れをAIが自動検知して修正。
3.  **Execute**: `Signature Orchestrator` が電子署名フローを起動し、関係者へ署名依頼を送信。
4.  **Archive**: 締結完了後、`Compliance Archiver` が契約書本体とエビデンスをセットで指定フォルダへ格納。

## 4. Available Resources
  - `assets/contract_clause_library.md`: 雇用契約・変更合意の特約条項ライブラリ。
- **Assets**:
  - `assets/contract_extraction_config.md`: 契約書AI抽出項目およびクラウドサイン連携用定義。
- **References**:
  - `references/e-contract_compliance_guide.md`: 電子署名法・電子帳簿保存法対応ガイドライン。

## 5. Operational Principles
*   **Legal Compliance**: 電子署名法および社内規程に準拠したプロセスを厳守し、法的有効性を担保する。
*   **Data Integrity**: システム間のデータ移動における欠損や改ざんを防ぐため、常にハッシュ値の検証やログの記録を行う。
*   **Seamless Transition**: 従来の紙ベースからの移行に際し、直感的なUIと明確なステータス表示で、全ステークホルダーの利便性を高める。
