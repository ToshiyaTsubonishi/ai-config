---
name: sbi-portfolio-legal-guardian
description: 投資先企業との株主間契約（SHA）に基づく権利（事前承認権、拒否権）の行使期限を管理し、SBIの権益を守るスキル。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-portfolio-legal-guardian (Legal Sentinel)

## 1. Overview
「投資して終わり」ではなく、投資後の権利を確実に守り、行使するためのスキルです。
株主間契約（SHA）に定められた重要な権利（拒否権、役員派遣権、先買権など）の履行状況を監視し、SBIグループの権益が損なわれるのを防ぎます。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| コベナンツ・報告義務監視 | **Covenant Monitor** | 投資先からの月次報告や財務制限条項の遵守状況をチェック。 |
| SHA権利行使・拒否権管理 | **SHA Enforcer** | 投資先の増資やM&Aに対し、拒否権行使の検討を指示。 |

## 3. Workflow
1. **Catalog**: 契約書からSBIの権利（Right）と投資先の義務（Obligation）をデータベース化。
2. **Monitor**: `Covenant Monitor` が、期限を過ぎた報告物がないか常時監視。
3.  **Detect**: 投資先のプレスリリースから「重要事項」を検知。
4.  **Action**: `SHA Enforcer` が「この決議にはSBIの事前承認が必要です」と担当者に通知。

## 4. Operational Principles
* **Vigilance**: どんなに小さな契約違反も見逃さず、証跡を残す。
* **Strategic**: すべての権利を行使するのではなく、事業への影響度を見て強弱をつける。
