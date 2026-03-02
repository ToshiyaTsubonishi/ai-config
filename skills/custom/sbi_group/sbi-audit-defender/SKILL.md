---
name: sbi-audit-defender
description: 外部監査人や規制当局（金融庁）からの検査に対し、必要な資料を即座に提示し、指摘事項への対応を支援する対監査防御スキル。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-audit-defender (Audit Shield)

## 1. Overview
金融庁検査や監査法人による会計監査を「守り」から「攻め」の姿勢に変えるスキルです。
資料依頼（PBCリスト）への対応を自動化し、過去の指摘事項との整合性をAIが検証することで、監査工数の削減と「指摘事項ゼロ」の両立を目指します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 監査準備・証跡自動収集 | **Audit Readiness Scanner** | 規定やマニュアルに基づき、必要なエビデンス（議事録、ログ）が揃っているか事前チェック。 |
| 監査人質疑・回答作成 | **Auditor Liaison Bot** | 監査人からの質問（Inquiry）を解析し、SBIグループの標準回答案を作成。 |

## 3. Workflow
1. **Index**: `Audit Readiness Scanner` が社内のドキュメント管理システムをスキャン。
2. **Alert**: 不足している証跡があれば、担当部署に自動通知。
3. **Receive**: 監査人からの質問状（CSV/Excel）を受領。
4. **Respond**: `Auditor Liaison Bot` が最適な回答と裏付け資料をセットで提示。

## 4. Operational Principles
* **Integrity**: 事実に基づかない回答は行わず、常に証拠（Evidence）を重視する。
* **Consistency**: 以前の回答と矛盾が生じないよう、回答履歴を管理する。
