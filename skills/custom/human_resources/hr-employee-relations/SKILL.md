---
name: hr-employee-relations
description: ハラスメント防止、メンタルヘルスケア、およびエンゲージメント向上施策を通じて、健全な組織風土を醸成するスキル。
version: 2.0.0
author: SBI Orchestrator
---
# hr-employee-relations (Culture Health)

## 1. Overview
組織の「見えない病気」を早期発見し、治療するスキルです。
エンゲージメントサーベイや相談窓口を通じて、従業員の本音を引き出し、働きがいのある職場を作ります。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| トラブル仲裁・相談 | **Conflict Mediator** | 中立的な立場で話を聞き、解決の糸口を探る。 |
| サーベイ実施・分析 | **Pulse Survey Analyst** | 高頻度のアンケートで、組織の状態変化をリアルタイム検知。 |

## 3. Workflow
1. **Survey**: `Pulse Survey Analyst` が週次の簡易アンケートを実施。
2.  **Detect**: 「特定の部署でスコアが急落」などのアラートを発報。
3.  **Resolve**: `Conflict Mediator` が、該当部署のメンバーから（匿名で）事情をヒアリング。

## 4. Operational Principles
*   **Psychological Safety**: 「何を言っても不利益を被らない」という安心感を醸成する。
*   **Action**: サーベイをやりっ放しにせず、必ず何らかのアクション（改善）に繋げる。
