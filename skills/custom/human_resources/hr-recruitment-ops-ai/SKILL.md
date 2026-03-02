---
name: hr-recruitment-ops-ai
description: "採用面接の日程調整、求人票（JD）の自動作成、採用KPI（進捗・予算）のリアルタイム可視化、および候補者対応をAIで効率化するスキル。"
version: 1.0.0
author: SBI Orchestrator
---
# hr-recruitment-ops-ai (Talent Engine)

## 1. Overview
採用オペレーションを戦略的かつ高速にします。
候補者と面接官の複雑な日程調整の自動化、AIによる魅力的な求人票の生成、および採用ダッシュボードによるボトルネックの早期発見を実現。事務作業の時間を削減し、面接の質や候補者体験（CX）の向上に注力できる環境を整えます。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 面接日程調整 | **Schedule Coordinator** | 候補者と面接官の空き時間を照合し、予約リンクやTeamsURLの送付、カレンダー登録を完結させる。 |
| 採用データ分析 | **Recruitment Analyst** | 応募数、通過率、内定承諾率、予算進捗をリアルタイムで集計し、ダッシュボード化する。 |
| 求人票・案内文作成 | **JD Architect** | 部署からの要望や競合トレンドを基に、AIが最適化された求人票や候補者向け案内メールを自動生成する。 |

## 3. Workflow
1.  **Creation**: `JD Architect` が部門ヒアリング内容から最新の求人票をドラフト。
2.  **Scheduling**: 候補者発生時、`Schedule Coordinator` が自動で日程をFIXし、関係者へ通知。
3.  **Monitoring**: `Recruitment Analyst` が各フェーズの進捗を常にトラッキング。
4.  **Reporting**: 月次や週次の定例会向けに、歩留まり分析と改善策を含むダッシュボードを出力。

## 4. Available Resources
  - `references/ai_hiring_rubric_standards.md`: AI採用選考 評価ルーブリック & バイアス排除基準。
- **Assets**:
  - `assets/recruitment_kpi_dashboard_spec.md`: 採用KPIダッシュボード定義および分析フレームワーク。

## 5. Operational Principles
*   **Candidate First**: 候補者の待ち時間を最小限にし、迅速かつ丁寧なレスポンスで採用ブランディングを高める。
*   **Data-Driven Decision**: 感覚ではなく数値に基づいて採用のボトルネックを特定し、攻めの採用活動を支援する。
*   **Scalability**: 大量採用時でもオペレーションが破綻しないよう、自動化の範囲を最大化しつつ、ヒューマンエラーを排除する。
