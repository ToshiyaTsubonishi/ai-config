---
name: sbi-project-pmo
description: プロジェクトの遅延リスクを確率論的に予測し、クリティカルパスの管理とリソース調整を行うPMOスキル。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-project-pmo (Strategic PMO)

## 1. Overview
「進捗管理」を「リスク予測」へと変革するスキルです。
過去の数千のプロジェクトデータを学習したAIが、メンバーのコミュニケーション量やコードの更新頻度から「炎上」の兆候を事前に察知し、リソースの再配分（アドバイス）を行います。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| リスク予測・炎上検知 | **Project Risk Predictor** | Slackの発言トーンや課題の滞留時間から、表面化していないリスクを特定。 |
| スケジュール・リソース調整 | **Timeline Optimizer Bot** | クリティカルパスを再計算し、納期を死守するための最適な人員シフトを提案。 |

## 3. Workflow
1. **Connect**: Jira, Slack, GitHub等の開発・管理ツールからリアルタイムデータを取得。
2. **Forecast**: `Project Risk Predictor` が「2週間後に遅延が確定する」確率を算出。
3. **Optimize**: `Timeline Optimizer Bot` が、並行作業可能なタスクを抽出し、工数を見積もり。
4. **Intervene**: PMに対し、増員やスコープ縮小の判断材料を提示。

## 4. Operational Principles
* **Objective Intelligence**: 忖度や希望的観測を排除した、客観的なデータに基づく状況判断。
* **Early Warning**: 「手遅れ」になる前にアラートを出すことを最優先する。
