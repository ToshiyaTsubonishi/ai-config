# Infinite Teller Architecture Reference (v2.2)

AGIバンカーを実現するための標準技術スタックとデータフロー。

## 1. Core Components

### Unified Model Gateway (UMG)
- **Role:** 全リクエストの集約・制御。
- **Tech:** Python (FastAPI), Redis (Rate Limit), Kong (API Gateway).
- **Features:**
    - **Multi-Tenant Router:** `X-Tenant-ID` ヘッダーによる銀行人格の切り替え。
    - **Guardrails:** NeMo Guardrailsによるプロンプトインジェクション防御。

### Cognitive Engine (The Brain)
- **LLM:** GPT-4 (Complex Logic) + FinBERT (Simple FAQ).
- **Memory:** Pinecone (Vector Store) for Long-term Context & RAG.
- **Planner:** LangChain (ReAct) for Task Decomposition.

### Value Transfer Layer (The Body)
- **Wallet:** MPC (2-of-3 Threshold Signature) using `tss-lib` (Go).
- **Approval:** Policy Engine (Open Policy Agent) for transaction validation.

## 2. Data Flow (Transaction)

1.  **User:** "5万円送金して" (Voice/Text)
2.  **UMG:** Intent="TRANSFER", Entity={"amount": 50000} を抽出。
3.  **Guardrail:** 金額が上限（10万円）以下であることを確認。
4.  **Agent:** 送金トランザクションを作成し、MPC署名リクエストを発行。
5.  **MPC Node:** Share A (Agent) と Share C (Server) で署名を生成。
6.  **Blockchain/Core:** トランザクション実行。
7.  **RLHF:** ユーザーの "ありがとう" (Feedback) を受け取り、報酬モデルを更新。

## 3. Infrastructure
- **Container:** Docker images managed by ECR.
- **Orchestration:** EKS (Amazon Elastic Kubernetes Service).
- **Security:** AWS Nitro Enclaves for MPC Key Management.

