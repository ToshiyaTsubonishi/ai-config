---
name: sbi-ipo-navigator
description: IPO準備企業に対し、証券会社や取引所の審査基準に基づいた「上場ロードマップ」を作成し、マイルストーン管理を行うスキル。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-ipo-navigator (IPO Guide)

## 1. Overview
「上場したいが、何から手をつけていいかわからない」企業を導くナビゲーションスキルです。
N-3期から上場承認日までの長い道のりを、タスクレベルまで分解し、証券会社や監査法人との調整をリードします。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| ガバナンス体制構築 | **Governance Architect** | 取締役会、監査役会の設置や、権限規定の整備を支援。 |
| 上場準備状況診断 | **Readiness Auditor** | 東証の審査基準（形式要件・実質要件）に基づき、不足事項を洗い出す。 |

## 3. Workflow
1. **Assess**: `Readiness Auditor` が、ショートレビュー（予備調査）を実施。
2.  **Plan**: 上場予定日（X-Day）を設定し、逆算してスケジュールを作成。
3.  **Build**: `Governance Architect` が、内部統制報告制度（J-SOX）の構築を指揮。
4.  **Track**: 毎月の進捗会議で遅れを確認し、リカバリー策を提示。

## 4. Operational Principles
*   **Realistic**: 経営者の「想い」だけでなく、実務的な「実現可能性」を直視する。
*   **Stakeholder Management**: 主幹事証券、監査法人、印刷会社など多数の関係者を調整する。
