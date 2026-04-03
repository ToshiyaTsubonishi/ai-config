# ai-config ドキュメント

## このドキュメントについて

ai-config を **動的 Skill / MCP 選択基盤** として運用・開発するためのドキュメントです。
selector / planner / execution boundary の責務分離を前提にしています。

## ドキュメント一覧

| ドキュメント | 内容 | 主な読者 |
|---|---|---|
| [概要ガイド](overview.md) | ai-config とは何か、なぜ必要か、何ができるか | 全員 |
| [Product Direction](product-direction.ja.md) | 方針、あるべき姿、目指す姿、優先順位を固定する north star | 全員 |
| [アーキテクチャガイド](architecture.md) | システム構成、データフロー、モジュール設計 | エンジニア |
| [運用ガイド](operations.md) | セットアップ、日常運用、トラブルシューティング | エンジニア・運用担当 |
| [開発者ガイド](development.md) | コード構造、テスト、拡張方法 | エンジニア |
| [Dispatch Externalization Plan](dispatch-externalization-plan.md) | result contract / ownership decision / dispatch 別 repo 化 plan | エンジニア |
| [Dispatch Runtime Completion Workflow](dispatch-runtime-completion-workflow.md) | runtime 外部化完遂の実行順序、gate、validation | エンジニア |
| [Rename Evaluation](rename-evaluation.md) | repo/package/CLI/env rename の影響評価と意思決定 | エンジニア |
