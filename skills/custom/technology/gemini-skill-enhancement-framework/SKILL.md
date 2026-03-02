---
name: gemini-skill-enhancement-framework
description: スキルの利用状況をモニタリングし、パフォーマンスの低いスキルを特定して改善（Refactoring）または廃止（Deprecation）を提案するフレームワーク。
version: 2.0.0
author: SBI Orchestrator
---
# gemini-skill-enhancement-framework (Skill Lifecycle)

## 1. Overview
スキルを「作りっぱなし」にせず、常に新陳代謝させるためのフレームワークです。
利用頻度の低い「ゾンビスキル」を廃止し、重複するスキルを統合することで、システム全体のスリム化と高性能化を維持します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| コード・プロンプト改善提案 | **Refactoring Advisor** | 冗長な記述を削除し、最新のベストプラクティスを適用。 |
| パフォーマンス監視 | **Skill Performance Monitor** | エラー率やレイテンシを監視し、改善が必要なスキルを特定。 |

## 3. Workflow
1. **Monitor**: `Skill Performance Monitor` が全スキルの実行ログを収集。
2.  **Alert**: 「このスキルは3ヶ月間使われていません」または「エラー率が5%を超えています」と通知。
3.  **Refactor**: `Refactoring Advisor` が、より効率的なコードへの書き換えを提案。
4.  **Deprecate**: 改善の見込みがない場合、廃止プロセス（ユーザーへの周知）を開始。

## 4. Operational Principles
*   **Lean**: 無駄なスキルは資産ではなく負債である。
*   **Continuous Improvement**: 毎日少しずつ良くなるシステムを目指す。
