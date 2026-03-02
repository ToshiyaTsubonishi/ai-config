---
name: sbi-it-administrator
description: 社内ネットワーク、SaaSアカウント、およびIT資産を一元管理し、セキュリティとコストを最適化する情シススキル。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-it-administrator (SysAdmin)

## 1. Overview
「情シス」の業務を自動化し、セキュアで快適なIT環境を提供するスキルです。
社員の入退社に伴うアカウント管理（LCM）や、ネットワークの安定稼働監視を無人化します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| ネットワーク監視・障害対応 | **Network Ops Bot** | トラフィック異常や機器故障を検知し、自動復旧または通知。 |
| SaaSライセンス・アカウント管理 | **SaaS License Optimizer** | 未使用アカウントの棚卸しと、契約プランの最適化。 |

## 3. Workflow
1. **Provision**: 入社日に合わせて、PCのキッティングとSaaSアカウント発行を完了。
2.  **Monitor**: `Network Ops Bot` が社内LANやVPNの帯域を監視。
3.  **Optimize**: `SaaS License Optimizer` が、「高いプランを使っているのに機能を使っていない」ユーザーをダウングレード。
4.  **Deprovision**: 退職と同時にアカウントを停止し、情報漏洩を防ぐ。

## 4. Operational Principles
*   **Security**: 利便性を損なわない範囲で、多要素認証（MFA）などのセキュリティ対策を強制する。
*   **Cost**: 固定費になりがちなITコストを、利用実態に合わせて変動費化する。
