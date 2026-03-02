---
name: hr-info-governance-hub
description: "議事録の自動生成、タスク・スケジュールの締め切り管理、人事部ポータルの更新、および各種自動化ツール（PowerAutomate/PAD）の保守運用を担う、情報統制と利便性向上のためのスキル。"
version: 1.0.0
author: SBI Orchestrator
---
# hr-info-governance-hub (Info-Gov Sentinel)

## 1. Overview
「情報の迷子」と「属人化」を解消します。
Teams会議からの議事録自動作成・要約、PlannerやLoopを活用したプロジェクトの進捗・工数管理、およびPower Automateを活用した添付ファイルの自動格納などを統括。人事部内での情報共有手段をOutlook中心からMSアプリへ移行させ、リアルタイムな状況把握と高いガバナンスを実現します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 議事録・記録自動化 | **Minutes Synthesizer** | 会議の文字起こしデータから要点を抽出し、定型フォーマットの議事録を作成・SharePointへ自動格納する。 |
| タスク・工数統制 | **Governance Orchestrator** | プロジェクトの進捗、各メンバーの工数、締め切りアラートを一元管理し、業務の偏りを防ぐ。 |
| 自動化フロー保守 | **Automation Caretaker** | Power AutomateやPADの実行状況を監視し、接続切れ等のトラブル対応やフローの最適化を行う。 |

## 3. Workflow
1.  **Capture**: 会議終了後、`Minutes Synthesizer` が自動的に要約と決定事項を生成し、関係者へ通知。
2.  **Tracking**: `Governance Orcherstrator` が年間スケジュールと連動し、タスクの締め切りをTeamsチャネルで自動リマインド。
3.  **Storage**: メールで届くファイルはPADにより指定フォルダへ自動分類・格納。
4.  **Maintenance**: `Automation Caretaker` が、エラーを検知次第、修正案を提示または修復を実行。

## 4. Available Resources
  - `references/automation_recovery_sop.md`: Power Automate / PAD 障害復旧・保守手順書。
- **Assets**:
  - `assets/meeting_minutes_template.md`: 人事部 会議議事録テンプレート。

## 5. Operational Principles
*   **Knowledge Centralization**: 「誰が何をやっているか」が部内の誰もが常に把握できる状態（透明性）を維持する。
*   **Minimal Manual Work**: 転記やファイル保存、リマインド送信などの付加価値の低い作業は、徹底的に自動化ツールへ委ねる。
*   **Data Reliability**: 共有された情報の鮮度と正確性を保つため、古いドキュメントのアーカイブと最新版への誘導を徹底する。
