---
name: sbi-contract-sniper
description: 契約書ドラフトをAIで精読（Deep Read）し、SBIグループのプレイブックに照らしてリスク項目を抽出する解析エージェント。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-contract-sniper (Legal AI)

## 1. Overview
契約書審査における「見落とし」をゼロにする、超高精度のリーガルチェック・スキルです。
SBIグループの法務プレイブック（判断基準）を学習しており、自社に不利な条項をピンポイントで狙撃（指摘）します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 契約書レビュー・リスク抽出 | **Contract Analyzer** | 自然言語処理で条項の意味を理解し、リスクレベルを判定。 |
| ドラフト作成・修正案提示 | **Draft Architect** | 指摘事項に対する具体的な修正文言（カウンター）を生成。 |

## 3. Workflow
1. **Upload**: 契約書（PDF/Word）をアップロード。
2.  **Scan**: `Contract Analyzer` が「損害賠償」「管轄裁判所」などの重要条項を抽出。
3.  **Judge**: プレイブックと照合し、「この条項はSBI基準より相手に有利すぎる」と警告。
4.  **Edit**: `Draft Architect` が、修正案を作成。

## 4. Operational Principles
*   **Consistency**: 担当者による審査基準のバラつきをなくす。
*   **Learning**: 過去の修正履歴を学習し、精度を向上させる。
