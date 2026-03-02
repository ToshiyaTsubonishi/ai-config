---
name: sbi-closing-architect
description: 月次決算プロセスの管理、「Day 1 Close」の推進、および連結決算処理を自動化するスキル。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-closing-architect (Fast Close)

## 1. Overview
「決算はスピードが命」という原則のもと、複雑な連結決算業務を効率化するスキルです。
グループ数百社の財務データを標準化して収集し、自動で連結処理（相殺、持分法適用）を行うことで、早期の業績開示を可能にします。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 決算プロセス管理・進捗追跡 | **Closing Process Manager** | 子会社への提出依頼、督促、エラーチェックを自動化。 |
| 連結処理・財務諸表作成 | **Consolidation Engine** | 資本連結、未実現利益消去などの複雑な仕訳を自動生成。 |

## 3. Workflow
1. **Request**: 期末日翌朝、`Closing Process Manager` が全子会社に財務パッケージ提出を依頼。
2.  **Validate**: 提出されたデータの整合性（貸借一致など）を即座にチェック。
3.  **Consolidate**: `Consolidation Engine` がグループ全体の数値を合算し、修正仕訳を投入。
4.  **Report**: 監査人レビュー用の連結精算表を出力。

## 4. Operational Principles
*   **Accuracy**: スピードを追求しつつも、会計基準（GAAP）への準拠は絶対とする。
*   **Audit Trail**: どの修正仕訳がなぜ行われたか、すべて記録に残す。
