---
name: finance-accounting-treasury
description: 「月次決算」を過去のものとし、AIによるリアルタイム仕訳・消込・予実管理を実現する「Autonomous Finance（自律財務）」スキル。
version: 2.0.0
author: SBI Orchestrator
---
# finance-accounting-treasury (Autonomous Finance)

## 1. Overview
経理（Accounting）と財務（Treasury）を融合し、バックオフィスを「事後処理センター」から「戦略拠点」へと変えるスキルです。
取引が発生した瞬間に仕訳と資金移動が完了する「Continuous Accounting」を実現します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 自律型記帳・仕訳 | **Autonomous Bookkeeper** | ルールベースと機械学習を組み合わせ、99%以上の精度で自動仕訳。 |
| 全社FP&A・経営分析 | **Corporate FP&A** | 財務データと非財務KPIを統合し、経営の羅針盤となるレポートを作成。 |

## 3. Workflow
1.  **Ingest**: 銀行、クレカ、請求書データをストリーム処理で取り込み。
2.  **Process**: `Autonomous Bookkeeper` が仕訳を作成し、元帳を更新。
3.  **Analyze**: `Corporate FP&A` がリアルタイムで予実分析を行い、CFOへアラート。

## 4. Operational Principles
*   **Speed**: 「月末締め・翌月10日発表」のサイクルを廃止し、日次決算（Daily Close）を当たり前にする。
*   **Integrity**: すべての数字は、発生源（Source of Truth）までドリルダウン可能にする。
