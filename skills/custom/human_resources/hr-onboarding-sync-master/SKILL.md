---
name: hr-onboarding-sync-master
description: "内定確定から入社、さらには転籍・出向受入に至るまでの人事情報を一元管理し、複数部署・システム間での情報共有と登録作業を自動同期させるスキル。"
version: 1.0.0
author: SBI Orchestrator
---
# hr-onboarding-sync-master (Onboarding Bridge)

## 1. Overview
採用チームから労務・手続きチームへのバトンタッチをワンストップ化します。
メールやファイルに分散していた内定者情報をSharePointやCOMPANY等のマスタへ自動反映し、入力ミスや連携漏れを排除。チームを越えた業務理解と、確実な入社準備フローの構築を支援します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 情報集約・正規化 | **Data Normalizer** | 採用ツールやFormsから取得した内定者情報を、COMPANY登録や管理表に適した形式に変換・クレンジングする。 |
| システム自動同期 | **Master Sync Agent** | SharePointの管理表、HPM入社管理表、COMPANY等へのデータ書き込みおよび更新を行う。 |
| 進捗アラート管理 | **Milestone Watcher** | 入社日までの各タスク（PC手配、情報登録、発令可否チェック）を監視し、遅延や漏れを自動通知する。 |

## 3. Workflow
1.  **Ingest**: `Data Normalizer` が入社確定情報を検知し、基本情報を構造化。
2.  **Dispatch**: `Master Sync Agent` が、SharePointの一括管理表を更新し、必要情報を各担当者へ自動通知。
3.  **Check**: `Milestone Watcher` がHPM入社管理表を定期監視し、「発令可」状態を自動判別して次工程へ。
4.  **Consolidate**: 転籍・出向等の外部情報のやり取りもメールから共通プラットフォーム（SharePoint等）へ集約管理。

## 4. Available Resources
  - `assets/digital_welcome_kit_spec.md`: デジタル・オンボーディング ウェルカムキット構成案。
  - `references/company_hpm_technical_spec.md`: COMPANY HPM (就労管理) データ構造・連携仕様書。
  - `assets/data_validation_regex_set.md`: 入社手続きデータのバリデーション正規表現集。
- **Assets**:
  - `assets/onboarding_sync_checklist.md`: 入社手続き・システム連携チェックリスト。
- **References**:
  - `references/onboarding_data_governance.md`: 入社情報のデータフローおよびガバナンス定義。

## 5. Operational Principles
*   **Single Source of Truth**: 情報は常に管理表を正とし、メールでの個別のやり取りによる先祖返りや食い違いを防ぐ。
*   **Proactive Notification**: 「待つ」時間を減らすため、情報の更新や期限接近を能動的にプッシュ通知する。
*   **Cross-Team Efficiency**: 採用と労務の知識の壁を越えられるよう、専門用語の解説や必要なエビデンスのチェックリストを自動提示する。
