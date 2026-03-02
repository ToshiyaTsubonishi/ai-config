---
name: sbi-evolution-manager
description: AIエージェントやスキルのパフォーマンスを自己評価（Self-Assessment）し、継続的な改善サイクル（Upgrading）を回す進化管理スキル。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-evolution-manager (Kaizen AI)

## 1. Overview
SBIグループのAIエコシステムが陳腐化しないよう、自律的に進化し続けるためのメタスキルです。
全エージェントの成績表をつけ、成績の悪いエージェントには再教育（リファクタリング）や配置転換（統廃合）を行います。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 自己評価・パフォーマンス分析 | **Self-Assessment Bot** | エージェントの回答精度やユーザー満足度を定量評価。 |
| アップグレード計画・実装 | **Upgrade Planner** | 改善点に基づき、コード修正やプロンプト更新の計画を立案。 |

## 3. Workflow
1. **Assess**: `Self-Assessment Bot` が週次レポートを作成。
2.  **Diagnose**: 「回答が遅い」「誤りが多い」といった課題を特定。
3.  **Plan**: `Upgrade Planner` が、GPT-4からGPT-5へのモデル変更や、検索ロジックの改善を提案。
4.  **Execute**: 人間の承認を得て、システムを更新。

## 4. Operational Principles
*   **Safety**: 進化の過程で、既存の機能を壊さない（回帰テストの徹底）。
*   **Transparency**: どのような変更が行われたか、リリースノートを自動生成する。
