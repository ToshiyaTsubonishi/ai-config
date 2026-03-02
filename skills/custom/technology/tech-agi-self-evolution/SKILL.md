---
name: tech-agi-self-evolution
description: AIエージェント自身が自分のコードやプロンプトを書き換え、性能を自律的に向上させる「自己進化」のメカニズムを実装するスキル。
version: 1.0.0
author: Gemini Skill Creator
---
# tech-agi-self-evolution (Recursive Improvement)

## 1. Overview
**What is this?**
SBIグループのAIシステムが、人間の介入なしに自らをアップグレードし続けるためのメタスキルです。
実行ログの分析、ボトルネックの特定、そしてコードの修正（Refactoring）を自律的に行い、システムのIQを高め続けます。

**When to use this?**
*   エージェントのエラー率が高止まりしている場合に、原因を特定して修正させる場合。
*   より効率的なプロンプト（Instructions）を自動生成させる場合。
*   古くなったスキルを統合・廃止し、システム全体をスリム化する場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| 進化の承認・ガバナンス | **Evolution Governor** | `../../agents/evolution-governor.md` |
| プロンプト最適化 | **Meta Prompt Optimizer** | `../../agents/meta-prompt-optimizer.md` |
| スキル・コードのリファクタリング | **Skill Refactorer** | `../../agents/skill-refactorer.md` |

### 2.2 Workflow
1.  **Monitor**: エージェントのパフォーマンス（成功率、速度）を監視。
2.  **Optimize**: `Meta Prompt Optimizer` が、より良い回答を引き出すプロンプトを生成。
3.  **Refactor**: `Skill Refactorer` が、重複したコードを統合。
4.  **Govern**: `Evolution Governor` が、変更内容が「経営理念」に反していないか最終チェックし、適用。

## 3. Bundled Resources
*   No specific assets listed.

## 4. Safety
*   **Runaway Prevention**: 自己修正のループが暴走しないよう、厳格な停止条件と承認プロセス（Human-in-the-loop）を設ける。