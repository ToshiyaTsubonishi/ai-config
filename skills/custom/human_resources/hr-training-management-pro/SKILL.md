---
name: hr-training-management-pro
description: "研修の企画、集客、班分け、当日の運営、事後のアンケート分析およびレポーティングをAIで統合的に管理・効率化するスキル。"
version: 1.0.0
author: SBI Orchestrator
---
# hr-training-management-pro (Learning Architect)

## 1. Overview
研修運営のあらゆるフェーズをDX化します。
参加者の属性（社、部署、スキル等）を考慮したAIによる最適な班分け、アンケート結果の自動集計と改善策の提言、さらには最新の法規制を反映したeラーニング教材の自動生成など、人材育成の質と効率を同時に高めます。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 研修運営・出席管理 | **Event Logistics Bot** | 案内の自動送付、欠席連絡の受付、QRコード等を用いたデジタルの出席管理を行う。 |
| AIグルーピング・分析 | **Pedagogy Analyst** | 多様な属性バランスを考慮した最適な班分け案の作成、および受講後アンケートの多角的分析・レポーティング。 |
| 教材・QA作成支援 | **Content Creator AI** | 規定や法規制を学習し、短時間のeラーニング教材や理解度テストのQA、研修案内文を自動生成する。 |

## 3. Workflow
1.  **Planning**: `Content Creator AI` が研修テーマに基づき、案内文と教材案を作成。
2.  **Logistics**: `Event Logistics Bot` が対象者へ案内を送り、出欠をリアルタイムで管理。
3.  **Grouping**: 開催前に `Pedagogy Analyst` が、過去データや参加者の属性を基に最適なグループ分けを実行。
4.  **Reporting**: 終了後、`Pedagogy Analyst` がアンケート結果（Forms）を解析し、改善点を含む報告書を自動作成。

## 4. Available Resources
  - `references/dss_mapping_definition.md`: デジタルスキル標準 (DSS) 2.0 準拠のスキルマッピング。
- **Assets**:
  - `assets/training_report_template.md`: 研修アンケートおよびAI分析レポートテンプレート。

## 5. Operational Principles
*   **Balance & Diversity**: グルーピングにおいては、学びの最大化のため、所属や職種が偏らないようアルゴリズムを調整する。
*   **Insight-Driven**: 単なる数値集計ではなく、自由記述欄から「本質的な不満やニーズ」を抽出することに注力する。
*   **Agility**: 変化の速い法規制や業務ルールを即座に教材へ反映できるよう、情報のアップデートを容易にする設計とする。
