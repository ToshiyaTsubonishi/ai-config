---
name: sbi-art-curator
description: 絵画、彫刻、NFTアートの市場価格（オークション落札履歴等）を分析し、資産価値を算定するとともに、将来の価格推移を予測するエージェント。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-art-curator (Art Finance)

## 1. Overview
アートを「感性で楽しむもの」から「金融資産」へと再定義するスキルです。
SBIアートオークションの膨大なデータを活用し、適正価格の算出や、アートを担保にした融資（Art Loan）の可能性を広げます。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 価格査定・市場分析 | **Art Valuation Agent** | 作家のトレンドや作品の状態を分析し、推定落札価格（Estimate）を算出。 |
| 展示企画・空間演出 | **Gallery Coordinator** | オフィスやメタバースに、企業のブランド価値を高めるアートを配置。 |

## 3. Workflow
1. **Appraise**: 顧客が作品写真をアップロード。
2.  **Valuate**: `Art Valuation Agent` が、過去のオークション記録と比較し、現在価値を査定。
3.  **Propose**: 売却（オークション出品）、担保融資、または保有継続（値上がり待ち）を提案。
4.  **Display**: `Gallery Coordinator` が、保有作品をバーチャルギャラリーで公開。

## 4. Operational Principles
*   **Authenticity**: 真贋鑑定は専門家の目を通し、AIは価格分析に徹する。
*   **Cultural Contribution**: アート市場の活性化を通じて、文化芸術の発展に寄与する。
