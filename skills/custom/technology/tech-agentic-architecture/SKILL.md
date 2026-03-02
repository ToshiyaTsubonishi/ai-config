---
name: tech-agentic-architecture
description: 複数の自律エージェントが協調して動くための「社会基盤（Gateway, Orchestrator）」を設計・構築するアーキテクチャスキル。
version: 1.0.0
author: Gemini Skill Creator
---
# tech-agentic-architecture (Agent Society)

## 1. Overview
**What is this?**
数百、数千のAIエージェントが同時に稼働する環境において、エージェント間の通信、認証、およびタスクのルーティングを制御するインフラストラクチャです。
単なるマイクロサービスではなく、エージェント同士が会話（Negotiation）して問題を解決する「社会」を構築します。

**When to use this?**
*   新しいエージェントをシステムに追加（Onboarding）する場合。
*   エージェント間の通信プロトコル（MCP等）を定義する場合。
*   外部システムとエージェントを接続するAPIゲートウェイを構築する場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| 外部接続・APIゲートウェイ | **Gateway Architect** | `../../agents/gateway-architect.md` |
| マルチエージェント協調制御 | **Multi-Agent Orchestrator** | `../../agents/multi-agent-orchestrator.md` |

### 2.2 Workflow
1.  **Request**: 外部からのリクエストを `Gateway Architect` が受領し、適切なエージェント群を選定。
2.  **Orchestrate**: `Multi-Agent Orchestrator` が、タスクを分解し、各エージェント（専門家）に割り振り。
3.  **Synthesize**: 各エージェントの成果物を統合し、最終回答を生成。

## 3. Bundled Resources
*   `assets/umg_template.py`: Universal Multi-Agent Gateway (UMG) の実装テンプレート
*   `assets/tenant_config_schema.json`: マルチテナント設定スキーマ

## 4. Safety
*   **Throttling**: エージェントの暴走によるリソース枯渇（DoS）を防ぐため、レートリミットを設ける。