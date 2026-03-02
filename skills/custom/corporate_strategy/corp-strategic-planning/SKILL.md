---
name: corp-strategic-planning
description: 経営目標の構造化（KPIツリー）と、グループ全体の戦略整合性を管理する、次世代経営企画スキル。
version: 2.0.0
author: SBI Orchestrator
---
# corp-strategic-planning (Strategy Command)

## 1. Overview
「全体戦略」と「個別戦略」を統合し、SBIグループの目指すべき方向を示す「戦略の羅針盤」です。
環境変化を先取りしたシナリオプランニングを行い、リソース配分をダイナミックに最適化します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| KPIツリー設計・連動 | **KPI Tree Architect** | KGI（最終目標）から現場のアクションに繋がるKPIへの分解。 |
| 戦略的市場調査 | **Market Intelligence Agent** | PEST分析、競合動向、および顧客トレンドのファクト収集。 |
| 戦略整合性・ガバナンス監査 | **Strategic Alignment Auditor** | 各部門の施策が全体の方針や経営理念から逸脱していないか審査。 |

## 3. Workflow
1. **Sense**: `pest-trend-scanner` で外部環境の「兆し」をキャッチ。
2. **Formulate**: `Strategic Planner`（`sbi-meta-orchestrator` 傘下）と連携し、中期経営計画を策定。
3. **Audit**: 実績値を `sbi-business-intelligence-core` でモニタリングし、計画を修正。

## 4. Operational Principles
* **Philosophy First**: 儲かるかではなく、正しいかを判断基準とする。
* **Backcasting**: 理想の未来から逆算した、野心的な目標設定。
