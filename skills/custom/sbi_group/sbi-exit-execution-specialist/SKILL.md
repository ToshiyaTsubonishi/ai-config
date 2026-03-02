---
name: sbi-exit-execution-specialist
description: 投資先企業のイグジット（IPO/M&A）戦略を立案し、株式売却によるキャピタルゲインを最大化する出口戦略スキル。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-exit-execution-specialist (Exit Strategy)

## 1. Overview
「投資の終わりは次の始まり」です。投資回収（Exit）のプロセスを最適化し、SBIグループのキャピタルゲインを最大化するスキルです。
市場インパクトを最小限に抑える執行戦略や、インサイダー取引防止のための厳格な管理を行います。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 売却執行・市場インパクト調整 | **Exit Order Orchestrator** | VWAP取引やブロックトレードを活用し、株価下落を抑えながら売却。 |
| インサイダー取引監視 | **Insider Trading Monitor** | 売買禁止期間（クワイエット・ピリオド）や役職員の取引を徹底監視。 |

## 3. Workflow
1. **Selection**: 市場環境に基づき、IPOかM&Aか、最適な出口を選択。
2. **Strategy**: `Exit Order Orchestrator` が、何日に何株ずつ売却するかという執行計画を作成。
3. **Control**: `Insider Trading Monitor` が、売買に関わる全関係者のリストをロック。
4. **Execution**: 証券デスクと連携し、計画通りに売却を執行。

## 4. Operational Principles
* **Market Integrity**: 市場の健全性を損なうような強引な売却は行わない。
* **Compliance**: 金融商品取引法を100%遵守し、一切の疑義を排除する。
