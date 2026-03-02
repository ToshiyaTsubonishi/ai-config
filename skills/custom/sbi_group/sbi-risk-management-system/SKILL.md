---
name: sbi-risk-management-system
description: 全社的なリスク管理規定に基づき、現場のリスクコントロール（RCSA）を支援するシステム運用スキル。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-risk-management-system (RCSA)

## 1. Overview
「リスク管理」を特別な業務ではなく、日常のルーチンに組み込むためのスキルです。
現場担当者が事故（事務ミス、苦情）を記録し、AIがその原因分析（Why-Why分析）と再発防止策の提案を行うことで、組織全体のレジリエンスを高めます。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 反社・サンクションチェック | **Compliance Guard** | 国内外のウォッチリストと照合し、不適切な相手との取引を遮断。 |
| オペレーショナルリスク分析 | **Operational Risk Analyst** | 事務ミスの傾向を分析し、共通するリスク要因を特定。 |

## 3. Workflow
1. **Record**: 現場担当者がインシデントを入力。
2. **Analyze**: `Operational Risk Analyst` が「類似事案が過去に3件発生」などの警告を表示。
3. **Control**: 新規取引の際、`Compliance Guard` が相手先の背景を自動スクリーニング。
4. **Report**: 月次のリスク管理委員会向けレポートを自動生成。

## 4. Operational Principles
* **Learning from Failure**: 失敗を責めるのではなく、組織の学び（KB）に変える。
* **Zero Tolerance for Antisal**: 反社会的勢力との関係遮断は、いかなる場合も例外を認めない。
