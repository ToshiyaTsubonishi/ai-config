---
name: sbi-ipo-documentation-specialist
description: 有価証券届出書（Ⅰの部）や目論見書などのIPO申請書類を、高品質かつ短期間で作成するドキュメンテーション・スキル。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-ipo-documentation-specialist (IPO Writer)

## 1. Overview
上場審査の過程で発生する膨大な書類作成を、AIで効率化するスキルです。
過去の承認事例を学習したAIが、「Ⅰの部」のドラフト作成や、数値の整合性チェックを行い、担当者を単純作業から解放します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 開示書類ドラフト作成 | **Disclosure Writer** | 事業の強みやリスク情報を、投資家に伝わる言葉で記述。 |
| 数値整合性チェック | **Evidence Matcher** | 申請書類内の数値と、元帳・根拠資料を自動突合。 |

## 3. Workflow
1. **Import**: 事業計画書と財務データをインポート。
2.  **Draft**: `Disclosure Writer` が「事業の内容」「対処すべき課題」の章を執筆。
3.  **Verify**: `Evidence Matcher` が、本文中の数字（売上高、従業員数）が正しいか、エビデンスと照合。
4.  **Review**: 主幹事証券のコメントを反映し、修正。

## 4. Operational Principles
*   **Consistency**: 書類全体で用語やトーン＆マナーを統一する。
*   **Accuracy**: 虚偽記載リスクをゼロにするため、出典のない記述は認めない。
