---
name: tech-mcp-engineering
description: "Model Context Protocol (MCP) を活用し、AIエージェントと社内DB・SaaS・APIを接続する標準化されたインターフェース（MCP Server）を設計・実装するエンジニアリングスキル。"
version: 2.0.0
author: SBI Orchestrator
---
# tech-mcp-engineering (Integration Fabric)

## 1. Overview
Anthropicが提唱する **Model Context Protocol (MCP)** に完全準拠し、SBIグループ内のサイロ化されたデータソース（顧客DB、社内規定Wiki、マーケットデータ、Trading API）を、AIエージェントが安全かつ統一的に利用できる形で公開するための技術基盤。
「個別開発」によるスパゲッティコードを排除し、**「プラグアンドプレイ」でのツール拡張**を実現する。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| MCPサーバー構築 | **MCP Server Architect** | Python (mcp-sdk) または TypeScript を用いて、特定のリソースに対する Read/Write/Call Tool 機能を公開するサーバーを実装する。 |
| リソース・ルーティング | **Context Bridge Engineer** | ユーザーのコンテキスト（文脈）に応じて、必要なMCPサーバーだけを動的に接続し、トークン節約とセキュリティを両立させる。 |
| 接続テスト | **Skill Linter** | `mcp-inspector` 等のツールを用い、実装されたサーバーがプロトコルに準拠しており、正常に通信できるか検証する。 |

## 3. Workflow
1.  **Schema Definition**: 接続対象のデータソース（例: PostgreSQL, Slack, Google Drive）のAPI仕様を分析し、MCPのリソース（Resources）およびツール（Tools）として定義する。
2.  **Implementation**:
    *   **Python**: `mcp` パッケージを使用。FastAPI等でのラップも考慮。
    *   **TypeScript**: `@modelcontextprotocol/sdk` を使用。
    *   *Rule*: 認証情報（API Key）は必ず環境変数から読み込むこと。コードにハードコードしない。
3.  **Security Integration**: `compliance-guard` と連携し、センシティブなデータ（PII, インサイダー情報）へのアクセスには承認フローを組み込む。
4.  **Deployment**: Dockerコンテナ化し、社内Kubernetes基盤（またはCloud Run）へデプロイ。STDIOまたはSSE（Server-Sent Events）での通信を確立する。

## 4. Production Standards (Strict)
*   **Protocol Compliance**: JSON-RPC 2.0 ベースのMCP仕様に厳密に準拠すること。
*   **Error Handling**: エラー発生時は、AIが理解可能な明確なエラーメッセージと、リカバリーのためのヒントを返すこと。
*   **Stateless**: サーバーは原則ステートレスに設計し、スケーラビリティを確保すること。
*   **Log Integration**: 全てのリクエスト/レスポンスを `audit-logger` に送信するミドルウェアを実装すること。
