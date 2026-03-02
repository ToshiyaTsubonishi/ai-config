# SBI Unified Model Gateway (UMG) Blueprint

**Version:** 2.0 (Battle-Hardened)
**Author:** SBI-AI-Strategy-Core

## 1. Concept
**"The Cognitive Router"**
あらゆる金融サービス（App/Web）と、あらゆるAIモデル（LLM/SLM）の間に位置し、認証・ルーティング・監査・防御を一元管理するミドルウェア。

## 2. Layered Architecture

### Layer 1: Input Guardrails (The Shield)
- **Role:** 悪意ある入力（Jailbreak, PII）を物理的に遮断する。
- **Tech:** Regex, NeMo Guardrails, Azure AI Content Safety.
- **Policy:** "Deny by Default"（怪しきは通さず）。

### Layer 2: Semantic Router (The Brain)
- **Role:** ユーザーの意図（Intent）を理解し、適切なエージェントへ振り分ける。
- **Logic:**
    - "残高教えて" -> `Banking Agent`
    - "NISAどう？" -> `Securities Agent` + `RAG`
    - "ハワイ行く" -> `Insurance Agent`
- **Multi-Tenant:** `X-Tenant-ID` ヘッダーにより、銀行ごとの振る舞い（Persona）を切り替える。

### Layer 3: Autonomous Agents (The Hands)
- **Role:** 具体的な業務ロジックを実行する。
- **Components:**
    - **Planner:** タスクを手順に分解する（ReAct）。
    - **Executor:** 外部API（勘定系、証券基盤）を叩く。
    - **Memory:** ユーザーの文脈（Context）を保持する。

### Layer 4: Infrastructure Adapters (The Legs)
- **Role:** レガシーシステム（Legacy）とWeb3基盤への接続。
- **Web3:** MPC Wallet (2-of-3 TSS) による署名代行。
- **Banking:** FIDO2認証済みのセキュアな勘定系API接続。

## 3. Deployment Strategy
- **Container:** Docker/Kubernetes (EKS/AKS)
- **Region:** AWS Tokyo (Data Sovereignty)
- **Scaling:** HPA (Horizontal Pod Autoscaler) based on Request Queue.

