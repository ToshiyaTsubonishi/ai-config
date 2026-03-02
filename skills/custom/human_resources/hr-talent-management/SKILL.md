---
name: hr-talent-management
description: 全社員のスキル、評価、キャリア志向をデータベース化し、最適な人材配置（タレントマネジメント）を実現するスキル。
version: 2.0.0
author: SBI Orchestrator
---
# hr-talent-management (Talent Optimization)

## 1. Overview
「人材」という最大の資産を有効活用するためのスキルです。
勘や経験に頼った人事異動を排し、データに基づいたマッチングで、組織のパフォーマンスと従業員の満足度を最大化します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| スキル不足解消・リスキリング支援 | **Skill Gap Bridger** | 配置転換に伴うスキルギャップを埋めるための支援を行う。 |
| 人材データ分析・最適配置 | **Talent Data Analyst** | 全社員のスキルデータベースとプロジェクト要件をマッチング。 |

## 3. Workflow
1. **Database**: `Talent Data Analyst` が社員の経歴、評価、スキルを構造化データとして管理。
2. **Search**: 新規プロジェクトの発足時に、必要な人材を検索。
3. **Bridge**: `Skill Gap Bridger` が、異動候補者に対し、着任までに必要な準備をサポート。

## 4. Operational Principles
*   **Transparency**: 異動の理由や期待される役割を明確に伝える。
*   **Diversity**: 多様なバックグラウンドを持つチームを組成し、イノベーションを促進する。
