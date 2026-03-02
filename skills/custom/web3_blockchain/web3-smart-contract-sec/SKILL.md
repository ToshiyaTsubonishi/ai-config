---
name: web3-smart-contract-sec
description: Solidity/Vyperのコードに対し、静的解析とファジング（Fuzzing）を組み合わせて、未知の脆弱性を発見するセキュリティ特化スキル。
version: 1.0.0
author: Gemini Skill Creator
---
# web3-smart-contract-sec (Auditor Pro)

## 1. Overview
**What is this?**
ブロックチェーン上の契約（スマートコントラクト）は、一度デプロイすると修正が困難であり、バグは致命的な資金流出に繋がります。
このスキルは、攻撃者が悪用する可能性のあるエッジケースを徹底的に洗い出し、修正案を提示します。

**When to use this?**
*   DeFiプロトコルのロジックに、Reentrancy（再入攻撃）の脆弱性がないか確認する場合。
*   ランダムな入力を大量に与えるファジングテストを行い、予期せぬ挙動を探す場合。
*   ガス代（手数料）を節約するためのコード最適化を行う場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| 静的解析・脆弱性スキャン | **Static Analysis Bot** | `../../agents/static-analysis-bot.md` |
| ファジング・不変条件テスト | **Symbolic Fuzzer Agent** | `../../agents/symbolic-fuzzer-agent.md` |

### 2.2 Workflow
1.  **Scan**: `Static Analysis Bot` がSlitherを実行し、基本的なミスを検出。
2.  **Fuzz**: `Symbolic Fuzzer Agent` がEchidnaを使い、数百万通りの入力パターンをテスト。
3.  **Optimize**: ガス代が高すぎる処理を特定し、改善案（Yulの使用など）を提示。

## 3. Bundled Resources
*   `assets/audit_checklist.md`: スマートコントラクト監査チェックリスト
*   `assets/vulnerability_database.csv`: 過去のハッキング事例データベース

## 4. Safety
*   **Zero Trust**: 外部からの呼び出しは全て攻撃であると仮定してコードを書く。