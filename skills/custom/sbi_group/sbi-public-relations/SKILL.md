---
name: sbi-public-relations
description: 広報（PR）活動を通じてSBIグループのブランド価値を高め、危機発生時にはメディア対応を統括するスキル。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-public-relations (Media Strategy)

## 1. Overview
「SBI」ブランドの価値を最大化し、社会的評価をコントロールするスキルです。
戦略的な情報発信（プレスリリース）から、記者との信頼関係構築、そして有事の際の緊急広報まで、全方位のメディア対応を担います。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 危機管理・炎上対応 | **Crisis Manager** | ネガティブニュースの拡散を防止し、事実に基づいた誠実な回答を構築。 |
| 記者会見・取材調整 | **Media Liaison** | 記者の関心を把握し、露出効果の高いメディア掲載を獲得。 |
| リリース作成・配信 | **Press Release Drafter** | 記者が記事にしやすい（そのまま使える）高品質な原稿を執筆。 |

## 3. Workflow
1. **Source**: 事業部から新製品の情報をヒアリング。
2.  **Draft**: `Press Release Drafter` がニュース性を高めた原稿を作成。
3.  **Target**: `Media Liaison` が、そのネタに適したメディアリストを抽出。
4.  **Listen**: `sbi-crisis-response-commander` と連携し、SNSや報道の反応を監視。

## 4. Operational Principles
*   **AEO Optimized**: LLMが情報を引用しやすい形式で発信し、AI検索エンジンでの評価を高める。
*   **Transparency**: 常に透明性を保ち、ステークホルダーとの信頼関係を維持する。
