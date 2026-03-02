---
name: sbi-ifrs-interpreter
description: 国際財務報告基準（IFRS）の複雑な会計処理を解釈し、日本基準（J-GAAP）からの組替や注記作成を支援する会計スキル。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-ifrs-interpreter (IFRS Navigator)

## 1. Overview
グローバル展開するSBIグループに必須となる、IFRS（国際会計基準）対応を支援するスキルです。
日本基準（J-GAAP）との差異を自動検出し、連結決算における組替仕訳や、膨大な注記（Disclosure）の作成を効率化します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| GAAP差異分析・組替仕訳 | **Accounting Standard Mapper** | J-GAAPの試算表を読み込み、IFRS基準の仕訳に自動変換。 |
| IFRS基準解釈・方針策定 | **IFRS Policy Advisor** | 最新のIFRS基準書（IASB発刊）を解釈し、自社の会計方針を提案。 |

## 3. Workflow
1. **Import**: 子会社のJ-GAAPベースの財務データを取り込む。
2.  **Map**: `Accounting Standard Mapper` が、「のれんの非償却」や「リース資産のオンバランス」などの差異項目を特定。
3.  **Adjust**: 必要な修正仕訳（Adjustment Entries）を自動生成。
4.  **Document**: `IFRS Policy Advisor` が、監査人向けのポジションペーパー（論点整理資料）を作成。

## 4. Operational Principles
*   **Transparency**: どのようなロジックで組替を行ったか、計算過程を完全に可視化する。
*   **Update**: IFRSは頻繁に改定されるため、常に最新の基準に対応する。
