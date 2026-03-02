# HR Bot RAG精度向上 メタデータ・タグ設計仕様書

## 1. 目的
生成AIを用いた人事問い合わせ対応（RAG）において、情報の取得漏れ（False Negative）や誤回答を防ぐため、ドキュメントに付与すべきメタデータ構造を定義する。

## 2. メタデータ項目定義 (Schema)

| タグ名 | 説明 | 例 / 選択肢 |
| :--- | :--- | :--- |
| `hr_domain` | 人事の業務領域 | `Payroll`, `Leave`, `Onboarding`, `Evaluation` |
| `content_type` | 書類の種類 | `Policy` (規程), `SOP` (手順書), `FAQ`, `Form` |
| `audience` | 対象となる従業員 | `All`, `FullTime`, `Contractor`, `Manager` |
| `effective_date`| 内容の施行・更新日 | `2025-04-01` |
| `expiration_date`| 内容の失効予定日 | `2026-03-31` |
| `legal_source` | 根拠となる法律 | `Labor_Standards_Act`, `Child_Care_Leave_Act` |
| `keywords` | 検索を補完する語句 | `育休`, `パパ`, `手当`, `手続き` |

## 3. RAGにおけるフィルタリング戦略
1.  **事前フィルタリング (Pre-Filtering)**:
    - ユーザーの属性（正社員か否か）に基づき、`audience`タグで検索対象を絞り込む。
2.  **日付フィルタリング**:
    - `expiration_date`が過去のものは検索対象から自動除外する。
3.  **ハイブリッド検索**:
    - ベクトル検索（意味の近さ）とメタデータによるキーワードマッチングを組み合わせ、規程名の正確な指定に対応する。

## 4. ナレッジ・ライフサイクル管理
- 新しい法改正情報を登録する際、古いドキュメントのメタデータを `Status: Deprecated` に即座に更新する自動化フロー（Power Automate連携）を推奨する。
