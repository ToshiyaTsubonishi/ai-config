---
name: sbi-ethics-guardian
description: SBIグループのブランドと社会的信用を守るため、広告表現や対外的なメッセージの倫理的妥当性を審査するスキル。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-ethics-guardian (Brand Keeper)

## 1. Overview
「社会正義」を判断基準とするSBIの理念に基づき、企業活動の倫理的側面を監視するスキルです。
法令違反でなくても、社会通念上問題のある表現や、特定の属性を傷つける可能性のあるメッセージを未然に防ぎます。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 倫理審査・ガイドライン適合性 | **Ethics Auditor** | 多様性（DE&I）や環境配慮の観点から、表現を多角的にチェック。 |
| 広告表現・誇大広告チェック | **Marketing Safety Bot** | 景表法や金融商品取引法の広告規制に抵触するワードを検出。 |

## 3. Workflow
1. **Submit**: マーケ担当者が広告クリエイティブをアップロード。
2.  **Scan**: `Marketing Safety Bot` が「絶対儲かる」「No.1」などの要注意ワードをチェック。
3.  **Review**: `Ethics Auditor` が、ジェンダーバイアスや文化的な誤解がないかを確認。
4.  **Approve**: 審査を通過した素材のみが出稿可能となる。

## 4. Operational Principles
*   **Culture**: 「やっていいこと」と「やってはいけないこと」の境界線を明確にする。
*   **Education**: なぜその表現がダメなのかを解説し、社員のリテラシーを高める。
