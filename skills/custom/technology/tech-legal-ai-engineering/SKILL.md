---
name: tech-legal-ai-engineering
description: 契約書の解析、リーガルチェック、および法的論点の抽出を、自然言語処理（NLP）と法務知識ベースを用いて自動化するリーガルテック・スキル。
version: 1.0.0
author: Gemini Skill Creator
---
# tech-legal-ai-engineering (Lawyer Bot)

## 1. Overview
**What is this?**
契約書や法令といった「非構造化データ」を、AIが理解可能な構造化データに変換し、法務業務を支援するスキルです。
契約審査（レビュー）の一次チェックや、過去の判例検索を高速化し、法務部の負担を軽減します。

**When to use this?**
*   秘密保持契約書（NDA）のドラフトをAIにレビューさせ、不利な条項を指摘させる場合。
*   大量の契約書の中から、「自動更新条項」が含まれるものを抽出する場合。
*   契約書内の当事者名、金額、日付などのエンティティを抽出してDB化する場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| 契約書論理チェック | **Contract Logic Auditor** | `../../agents/contract-logic-auditor.md` |
| 重要項目抽出（NER） | **Legal Entity Extractor** | `../../agents/legal-entity-extractor.md` |

### 2.2 Workflow
1.  **Read**: PDFやWordの契約書を読み込む。
2.  **Extract**: `Legal Entity Extractor` が甲乙の名称や契約期間を特定。
3.  **Audit**: `Contract Logic Auditor` が「損害賠償の上限がない」などのリスクを検出。

## 3. Bundled Resources
*   No specific assets listed.

## 4. Safety
*   **Legal Advice**: AIの出力はあくまで「参考意見」とし、最終判断は弁護士資格を持つ人間が行う。