---
name: strategy-corporate-planning
description: SBIグループの全体戦略に基づき、各事業部門のロードマップ策定、KPI管理、およびリソース配分を最適化する経営企画スキル。
version: 1.0.0
author: Gemini Skill Creator
---
# strategy-corporate-planning (Group Strategy)

## 1. Overview
**What is this?**
グループ各社の「全体最適」を実現するためのスキルです。
「5つの経営理念」を軸とした、中長期的なビジョンの策定から、日次のKPI管理、そして不採算事業の撤退判断まで、経営の屋台骨を支えます。

**When to use this?**
*   グループ全体のポートフォリオ（事業構成）を見直す場合。
*   経営目標（KGI）を達成するための、各部門への先行指標（KPI）を割り振る場合。
*   PEST分析に基づき、地政学的リスクや技術革新を戦略に組み込む場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| トレンドスキャン・PEST分析 | **PEST Trend Scanner** | `../../agents/pest-trend-scanner.md` |
| シナリオプランニング | **Scenario Strategist Bot** | `../../agents/scenario-strategist-bot.md` |

### 2.2 Workflow
1.  **Scan**: `PEST Trend Scanner` が外部環境（政治、経済、社会、技術）のメガトレンドを抽出。
2.  **Hypothesize**: `Scenario Strategist Bot` が「最良・ベース・最悪」の3つの未来シナリオを描画。
3.  **Execute**: 各シナリオにおける、SBIのレジリエンス（強靭性）を評価し、対策を立案。

## 3. Bundled Resources
*   `STRATEGY_WORKFLOW.md`: 経営企画ワークフロー標準

## 4. Safety
*   **Logical Consistency**: 戦略の論理（なぜ今、それをするのか）に飛躍がないか、徹底的に検証する。
*   **Philosophy Alignment**: どんなに儲かるビジネスであっても、経営理念に反するものは却下する。