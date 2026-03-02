---
name: sbi-ipo-labor-compliance
description: 未払い残業代や社会保険未加入などの労務リスクを解消し、上場審査に耐えうる労務管理体制を構築するスキル。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-ipo-labor-compliance (Labor Clean-up)

## 1. Overview
ベンチャー企業がIPOする際、最も躓きやすい「労務問題」を解決するスキルです。
過去2年分の勤怠データを洗い直し、未払い残業代があれば精算するとともに、労基法に完全準拠した規定を整備します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 就業規則・規定改定 | **HR Policy Modernizer** | 最新の法改正（働き方改革関連法等）に対応した規定を作成。 |
| 労務監査・未払い残業計算 | **Labor Audit Bot** | 隠れ残業を検出し、潜在債務（未払い賃金）を計算。 |

## 3. Workflow
1. **Audit**: `Labor Audit Bot` が、入退室ログとPCログを突合し、サービス残業の実態を調査。
2.  **Calculate**: 未払い賃金の総額を算出し、引当金を計上。
3.  **Correct**: `HR Policy Modernizer` が、実態に合わなくなった古い就業規則を改定。
4.  **Report**: 審査対応用の「労務改善報告書」を作成。

## 4. Operational Principles
*   **Compliance**: グレーゾーンを残さず、白黒はっきりさせる（White-collar Exemptionの適用厳格化など）。
*   **Trust**: 従業員との信頼関係を壊さないよう、誠実な対応を行う。
