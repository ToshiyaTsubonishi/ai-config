---
name: rwa-token-lifecycle-ops
description: 現実資産（不動産、債権等）から発生した収益を計算し、スマートコントラクト経由で自動分配（Dividend）する運用スキル。
version: 2.0.0
author: SBI Orchestrator
---
# rwa-token-lifecycle-ops (Token Dividend)

## 1. Overview
セキュリティトークン（STO）の「配当」や「償還」を、自動化するスキルです。
不動産の賃料収入や、ローンの利息収入をトークン保有者のウォレットへ、ガス代を抑えつつ正確に届けます。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 配当計算・自動分配 | **Dividend Distributor** | 権利確定日の保有量に基づいて、USDC等を一括送金。 |
| 発行・償還（Mint/Burn）管理 | **Token Mint-Burn Bot** | 資産の取得・売却に合わせて、トークン供給量を調整。 |

## 3. Workflow
1. **Check**: オフチェーンの銀行口座に入金（賃料等）があったことを確認。
2.  **Calculate**: `Dividend Distributor` が、源泉徴収税を控除した分配可能額を算出。
3.  **Transfer**: スマートコントラクトを叩き、投資家へ送金。
4.  **Reporting**: 支払調書データを作成。

## 4. Operational Principles
*   **Accuracy**: 金融取引としての正確性を最優先する。
*   **Transparency**: 分配の履歴はすべてオンチェーンで確認できるようにする。
