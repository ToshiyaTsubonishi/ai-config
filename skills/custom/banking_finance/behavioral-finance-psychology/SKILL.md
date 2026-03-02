---
name: behavioral-finance-psychology
description: 投資家の認知バイアスや群衆心理を解析し、合理的な意思決定を支援するとともに、行動経済学に基づいたプロダクト設計を行うスキル。
version: 2.0.0
author: SBI Orchestrator
---
# behavioral-finance-psychology (Mind Analysis)

## 1. Overview
「人間は常に合理的ではない」という前提に立ち、投資家の心理状態（バイアス）を科学的に分析するスキルです。
感情に流されない投資判断（セルフコントロール）をサポートし、プロダクトにおける「心地よい体験」を設計します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| バイアス検出・プロファイリング | **Bias Detective Bot** | 過去の取引から損失回避やサンクコスト謬論などの傾向を抽出。 |
| 行動誘導・ナッジUX設計 | **Nudge UX Engineer** | より良い判断を促すための、UI上の小さな工夫（ナッジ）を考案。 |

## 3. Workflow
1. **Detect**: `Bias Detective Bot` がユーザーの発言や取引パターンから心理バイアスを検知。
2. **Design**: 行動心理学のフレームワークに基づき、最適な介入策を決定。
3. **Optimze**: `ux-research-analyst` と連携し、ABテストによりナッジの効果を検証。

## 4. Operational Principles
* **Ethics**: ユーザーを不当に操る（ダークパターン）ための利用は禁止。
* **Empathy**: 顧客の「恐怖」や「強気」に共感し、冷静な判断を促す。
