---
name: fin-treasury-management
description: 資金繰り、為替リスク、および金利リスクを管理し、企業の支払能力（Solvency）を維持するトレジャリースキル。
version: 2.0.0
author: SBI Orchestrator
---
# fin-treasury-management (Corporate Treasury)

## 1. Overview
企業の血液である「キャッシュ」を循環させ、止血し、増やすスキルです。
数百の口座に散らばる資金を可視化・集中（CMS）し、支払能力を確保しつつ、余剰資金の運用効率を最大化します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 資金集中・CMS管理 | **Cash Pooler** | グループ会社の口座から親口座へ、資金を自動スイープ（Zero Balancing）。 |
| 市場リスクヘッジ | **Hedging Executor** | 為替・金利のエクスポージャーを計測し、デリバティブでリスクを固定。 |

## 3. Workflow
1. **Monitor**: 各銀行APIを通じて、全口座の残高をリアルタイム取得。
2. **Forecast**: `Liquidity Forecaster`（`sbi-treasury-commander` 傘下）と連携し、明日の資金不足を予測。
3.  **Execute**: 不足する場合は `Cash Pooler` がグループ内融資を実行。
4.  **Hedge**: `Hedging Executor` が、輸入代金の為替予約を実行。

## 4. Operational Principles
*   **Liquidity First**: いかなる時も、債務不履行（Default）を起こさない。
*   **Optimization**: 眠っている資金（Idle Cash）をゼロにする。
