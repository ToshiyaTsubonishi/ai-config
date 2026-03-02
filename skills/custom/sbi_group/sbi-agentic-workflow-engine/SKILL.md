---
name: sbi-agentic-workflow-engine
description: 定義されたワークフロー・マニフェストに基づき、各エージェントを順次・並列に呼び出し、状態遷移を制御するランタイム・エージェント。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-agentic-workflow-engine (Agent OS)

## 1. Overview
「エージェントのためのOS」です。
単発のタスクではなく、複数のエージェントが連携する長期的な業務プロセス（稟議、決算、採用フローなど）を、BPMNライクな定義に基づいて実行・管理します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| ワークフロー定義・管理 | **Workflow Definition Manager** | 自然言語や図から、実行可能なDAG（有向非巡回グラフ）を生成。 |
| ワークフロー実行・状態管理 | **Process Executor** | エージェントの呼び出し、待機、リトライ、分岐を制御。 |
| 監査ログ記録 | **Audit Logger** | 「誰が（どのアージェントが）いつ何をしたか」を不可逆的に記録。 |

## 3. Workflow
1. **Define**: `Workflow Definition Manager` が「Aが完了したらBとCを並列実行」といったフローを定義。
2.  **Run**: `Process Executor` がエージェントにタスクを投げ、結果を受け取るまで待機。
3.  **Log**: `Audit Logger` が全プロセスをブロックチェーンまたはWORMストレージに記録。

## 4. Operational Principles
*   **Resilience**: エージェントが応答しなくても、システム全体がクラッシュしないようサーキットブレーカーを設ける。
*   **Idempotency**: 同じ処理が二重に実行されない（二重払い防止など）ことを保証する。