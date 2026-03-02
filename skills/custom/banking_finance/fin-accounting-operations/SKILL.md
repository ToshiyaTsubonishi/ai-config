---
name: fin-accounting-operations
description: 請求書処理、経費精算、決算仕訳などの日常的な経理業務をAIで自動化するスキル。
version: 2.0.0
author: SBI Orchestrator
---
# fin-accounting-operations (Accounting 2.0)

## 1. Overview
「人間は判断し、AIは記録する」経理業務の完全自動化（Autonomous Accounting）スキルです。
インボイス制度や電子帳簿保存法に対応しつつ、取引の発生から記帳、支払いまでをリアルタイムで完結させます。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 自動仕訳・証憑データ化 | **Journal Entry Bot** | 領収書や請求書をAI-OCRで読み取り、勘定科目を高精度に推論。 |
| 証憑要件チェック（インボイス） | **Receipt Scanner AI** | 適格請求書発行事業者の登録番号確認と、法要件のチェックを自動化。 |

## 3. Workflow
1. **Intake**: 社員がSlackや専用アプリから証憑（領収書等）をアップロード。
2. **Validate**: `Receipt Scanner AI` が真正性と形式をチェック。
3. **Record**: `Autonomous Bookkeeper`（`finance-accounting-treasury` 傘下）と連携し、ERPへの自動投入。

## 4. Operational Principles
* **Accuracy**: 金融機関としての厳格な仕訳精度。
* **Compliance Ready**: いつ税務調査が入っても即座に対応できる証跡管理。
