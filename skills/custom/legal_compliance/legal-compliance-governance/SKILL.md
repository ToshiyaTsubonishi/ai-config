---
name: legal-compliance-governance
description: 法令遵守（コンプライアンス）と企業倫理（Ethics）を、AIの判断プロセスに組み込み、リスクを未然に防ぐスキル。
version: 2.0.0
author: SBI Orchestrator
---
# legal-compliance-governance (AI Ethics & Rules)

## 1. Overview
AIが「暴走」しないよう、倫理とルールの枠組みを嵌めるスキルです。
AIの判断における公平性を監査し、また社内規定を最新の法令に合わせて自動的にメンテナンスします。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| AI倫理監査・バイアス検知 | **AI Ethics Auditor** | AIの出力が差別的でないか、企業の価値観に合っているかをチェック。 |
| 社内規定の標準化・改定 | **Rule Standardizer** | 法改正に合わせて就業規則やセキュリティ規定をアップデート。 |

## 3. Workflow
1. **Audit**: `AI Ethics Auditor` が定期的にAIの会話ログをサンプリング。
2.  **Monitor**: `Rule Standardizer` が官報や法令データベースを監視。
3.  **Update**: 法律が変われば、関連する社内規定の改定案を自動生成。

## 4. Operational Principles
*   **Human-in-the-loop**: 倫理的な判断は最終的に人間が行う。
*   **Explainability**: なぜその判断が倫理的でないのか、理由を説明できるようにする。
