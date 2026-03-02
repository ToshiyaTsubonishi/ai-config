---
name: gemini-skill-quality-governance
description: AIスキルの品質、セキュリティ、およびライフサイクル（作成〜廃止）を管理し、システムの健全性を保つガバナンス・スキル。
version: 2.0.0
author: SBI Orchestrator
---
# gemini-skill-quality-governance (Skill Police)

## 1. Overview
SBIグループの品質基準（Quality Standard）を満たしたスキルのみが本番稼働できるようにするゲートキーパーです。
セキュリティ脆弱性、ライセンス違反、そして「使いにくさ」を排除します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| スキル監査・品質チェック | **Skill Auditor** | 定期的に全スキルをスキャンし、基準違反を検出。 |
| ライフサイクル管理・廃止 | **Lifecycle Coordinator** | スキルのバージョン管理と、安全な廃止プロセスを指揮。 |

## 3. Workflow
1. **Scan**: `Skill Auditor` が毎日全スキルをクロール。
2.  **Flag**: 「記述が不足している」「リンク切れがある」スキルに警告フラグを立てる。
3.  **Correct**: `Lifecycle Coordinator` が担当者に修正期限を設定して通知。
4.  **Suspend**: 期限内に修正されない場合、スキルを一時停止。

## 4. Operational Principles
*   **Quality First**: 低品質なスキルは、ない方がマシである。
*   **Security**: 脆弱性のあるスキルは即時停止する。
