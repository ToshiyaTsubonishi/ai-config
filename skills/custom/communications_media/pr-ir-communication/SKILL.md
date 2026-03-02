---
name: pr-ir-communication
description: 投資家（LP/株主）に対し、SBIの将来性を物語（ナラティブ）として伝え、株価や時価総額の向上を支援するエクイティ・ストーリースキル。
version: 2.0.0
author: SBI Orchestrator
---
# pr-ir-communication (Equity Story)

## 1. Overview
数字の羅列である決算情報を、投資家が「買いたい」と思うような魅力的な成長物語（Equity Story）に変換するスキルです。
機関投資家のセンチメント（感情）を分析し、期待値コントロールを行います。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| エクイティ・ナラティブ作成 | **Equity Narrative Crafter** | 財務数値と事業戦略を結びつけ、将来のキャッシュフローへの確信を与える。 |
| 投資家センチメント分析 | **Investor Sentiment Analyst** | 市場の「声」を聞き、IR活動の効果を測定。 |

## 3. Workflow
1. **Analyze**: `Investor Sentiment Analyst` がアナリストレポートや空売り残高を分析。
2.  **Draft**: `Equity Narrative Crafter` が、「なぜ今SBIなのか」を説くプレゼン資料を作成。
3.  **Deliver**: 決算説明会や統合報告書を通じて発信。

## 4. Operational Principles
*   **Consistency**: 短期的な株価対策で方針をコロコロ変えず、長期的なビジョンを一貫して伝える。
*   **Dialogue**: 一方的な説明ではなく、投資家との対話を重視する。
