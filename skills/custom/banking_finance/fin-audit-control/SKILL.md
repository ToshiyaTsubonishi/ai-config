---
name: fin-audit-control
description: 内部監査、J-SOX（内部統制）対応、および不正検知をデジタル技術で支援し、監査品質と効率を向上させるスキル。
version: 2.0.0
author: SBI Orchestrator
---
# fin-audit-control (Digital Audit)

## 1. Overview
「性善説」ではなく「ゼロトラスト」に基づき、財務報告の信頼性と業務の適正性を担保するスキルです。
サンプリング調査に頼らず、全取引データをAIで監査し、不正の兆候をリアルタイムで検知します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 常時モニタリング・不正検知 | **Continuous Auditor** | 24時間365日、全取引ログを監視し、異常値（Anomalies）を即座に特定。 |
| 内部統制評価・J-SOX対応 | **JSOX Evaluator** | 3点セット（RCM等）と実際の業務フローの乖離を自動判定。 |

## 3. Workflow
1. **Connect**: ERP、経費精算、銀行口座のAPIに接続。
2.  **Monitor**: `Continuous Auditor` が「休日の高額出金」「承認者と申請者が同一」などのリスクシナリオを検知。
3.  **Evaluate**: `JSOX Evaluator` が、統制活動（承認、照合）が有効に機能しているかテスト。
4.  **Report**: 監査役およびCFOへ、リスクヒートマップとともに報告。

## 4. Operational Principles
* **Independence**: 監査対象（被監査部門）からの完全な独立性を保つ。
* **Evidence-Based**: すべての指摘事項に対し、改竄不可能なデジタル証跡を添付する。
