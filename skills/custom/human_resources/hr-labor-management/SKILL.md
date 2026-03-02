---
name: hr-labor-management
description: 勤怠管理、給与計算、および労務トラブルの予防を自動化し、適法かつ効率的な労務オペレーションを実現するスキル。
version: 2.0.0
author: SBI Orchestrator
---
# hr-labor-management (Labor Ops)

## 1. Overview
「働き方改革」を推進し、コンプライアンスと生産性を両立させるスキルです。
36協定の遵守監視から給与計算の自動化まで、労務管理の全プロセスをカバーします。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 勤怠監査・過重労働防止 | **Attendance Auditor** | サービス残業を撲滅するため、PCログと打刻の乖離をチェック。 |
| 給与計算・明細発行 | **Payroll Calculator** | 複雑な手当計算や社会保険料の控除をミスなく実行。 |

## 3. Workflow
1. **Track**: 勤怠システムとPC稼働ログを同期。
2. **Alert**: 残業時間が上限に近づいた社員と上司に通知。
3. **Calc**: 月末に勤怠を締め、給与計算を実行して振込データを作成。

## 4. Operational Principles
*   **Compliance**: 労働基準法を厳守する。
*   **Accuracy**: 給与計算において1円のミスも許さない。
