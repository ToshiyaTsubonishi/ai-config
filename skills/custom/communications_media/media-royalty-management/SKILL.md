---
name: media-royalty-management
description: デジタルコンテンツの利用実績をトラッキングし、権利者へのロイヤリティ分配金額を自動算出・決済するスキル。
version: 2.0.0
author: SBI Orchestrator
---
# media-royalty-management (IP Ledger)

## 1. Overview
複雑な著作権契約に基づくロイヤリティ計算を、ブロックチェーンとスマートコントラクトで透明化・自動化するスキルです。
「誰が、いつ、どこで」コンテンツを利用したかを正確に把握し、権利者へ公正な対価を分配します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 利用実績照合・分配計算 | **Royalty Ledger Auditor** | 契約書と利用ログを突合し、支払額を確定。 |

## 3. Workflow
1. **Monitor**: ストリーミング配信やNFT取引のログを収集。
2.  **Calculate**: `Royalty Ledger Auditor` が、レベニューシェア率に基づき分配額を計算。
3.  **Pay**: スマートコントラクトを通じて、クリエイターのウォレットへ即時送金。

## 4. Operational Principles
*   **Transparency**: 計算ロジックを公開し、権利者がいつでも検証できるようにする。
*   **Accuracy**: 1円（または1wei）単位での正確な計算を行う。
