---
name: sbi-fund-admin-controller
description: 投資ファンドの管理業務（Fund Administration）を自動化し、投資家への報告（Reporting）とキャピタルコールを効率化するスキル。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-fund-admin-controller (Fund Administrator)

## 1. Overview
VC、PE、または暗号資産ファンドのバックオフィス業務を自動化するスキルです。
投資家（LP）との金銭的なやり取り（キャピタルコール、分配）や、複雑なパフォーマンス計算をミスなく、かつタイムリーに実行します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| キャピタルコール通知・管理 | **Capital Call Bot** | 投資実行に必要な資金をLPから正確な比率で呼び出す。 |
| パフォーマンス・運用報告 | **Reporting Analyst** | IRRやTVPIを計算し、投資家向けの定期報告書を作成。 |

## 3. Workflow
1. **Trigger**: 投資委員会で出資が決定。
2. **Calculate**: `Capital Call Bot` が、各投資家の未充当コミットメント額を確認し、請求額を算出。
3. **Send**: キャピタルコール通知を署名付きで送信。
4. **Report**: 四半期末に `Reporting Analyst` が、ポートフォリオ企業の最新時価を反映したレポートを作成。

## 4. Operational Principles
* **Compliance**: ファンドの投資契約（LPA）を遵守した資金管理を行う。
* **Investor Relations**: 投資家からの残高照会などに即座に回答し、信頼を高める。
