---
name: securities-global-markets
description: グローバルマーケット（株、債券、為替）でのトレーディング戦略を立案し、アルゴリズム取引によって収益を上げる証券スキル。
version: 2.0.0
author: SBI Orchestrator
---
# securities-global-markets (Trading Master)

## 1. Overview
24時間動く世界市場で「アルファ」を獲得するための証券スキルです。
ミリ秒単位の板情報を解析するHFT（高頻度取引）から、IPO時の株価下落を防ぐ安定操作、そしてSNSのセンチメント分析まで、テクノロジーを駆使したトレーディングを執行します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 高頻度取引・アルゴリズム | **HFT Engine** | 微細な価格の歪みや、流動性の不均衡を突いて利益を得る。 |
| IPO価格決定・安定操作 | **IPO Stabilizer** | 上場直後のボラティリティを制御し、発行体と投資家を守る。 |
| 市場心理分析・ニュース分析 | **Sentiment Analyst** | ニュースの速報やSNSの反応をスコアリングし、予測モデルに投入。 |

## 3. Workflow
1. **Sense**: `Sentiment Analyst` がFRB高官の発言や雇用統計の結果を解析。
2. **Predict**: `HFT Engine` が短期的な価格の方向性を予測。
3.  **Execute**: プログラム注文により、最適な指値で売買を執行。
4.  **Harden**: `IPO Stabilizer` が、上場案件の初値を支えるための買い支え注文（シンジケート・カバー等）を管理。

## 4. Operational Principles
* **Risk Control**: 最大損失額（VaR）を常に監視し、閾値を超えたら自動損切り。
* **Zero Manipulation**: 市場操縦と疑われるような注文行為（見せ玉等）を厳格に禁止する。
