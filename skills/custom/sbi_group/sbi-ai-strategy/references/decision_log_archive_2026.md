# Decision Log Archive: SBI AGI-Transformation 2026

**Project:** Infinite Teller (The Autonomous Financial Life-OS)

**Decision Maker:** Strategy Core (AI)

## Decision 001: Cognitive Architecture

- **Issue:** AGIの「知能」と「人格」をどのように実装し、永続化させるか？
    
- **Options:**
    
    - A. Model-Coupled (特定のLLMのコンテキストウィンドウに全て依存する)
        
    - B. Cognitive Substrate (推論エンジンと、記憶・人格・ツールを分離する)
        
- **Decision:** **B. Cognitive Substrate (認知的基盤の分離)**
    
- **Reasoning:**
    
    - **Intelligence Portability:** AGIの価値は「モデルの賢さ」ではなく、「ユーザーを深く理解した文脈（Context）」にある。推論エンジン（GPT/Claude等）は交換可能なCPUとして扱い、人格や長期記憶（User Profile/Memory）はOS層で保持する。
        
    - **Stateful Entity:** 1回ごとのRequest/Responseで終わるAPI呼び出しではなく、エージェントが「状態（State）」を持ち続け、ユーザーが寝ている間も自律思考し続ける永続的なプロセスとして設計するため。
        
    - **Ecosystem Agnostic:** 特定のプラットフォームに依存せず、AGIが将来的にユーザーのデバイス（Edge AI）や異なるメタバース間を移動可能にするため。
        

## Decision 002: Economic Agency Implementation

- **Issue:** AGIにどのような「経済的権限」を与え、その正当性を担保するか？
    
- **Options:**
    
    - A. Key Custody (秘密鍵を安全に保管し、人間が承認する)
        
    - B. Programmatic Trust (署名権限を委譲し、スマートコントラクトで統制する)
        
- **Decision:** **B. Programmatic Trust (プログラムされた信認)**
    
- **Reasoning:**
    
    - **Autonomous Economic Actor:** AGIを単なるツールではなく、限定的な法的・経済的主体（Agent as a Legal Wrapper）として扱う。MPC（マルチパーティ計算）を基盤としつつ、さらに「契約（Smart Contract）」によって「1万円以下の決済なら即時実行、それ以上はMultisig」といった権限規定をコードで強制する。
        
    - **Verifiable Action:** 「なぜその取引を行ったか」という思考プロセス自体をチェーン上または改ざん不能なログに記録し、監査可能性（Auditability）ではなく証明可能性（Provability）を担保する。
        
    - **Speed of Finance:** 人間の承認速度（Human Latency）を排除し、ミリ秒単位の市場変動に対応した超高速・高頻度の資産運用を実現するため。
        

## Decision 003: Alignment & Objective Function

- **Issue:** AGIの行動原理（目的関数）を何に設定するか？
    
- **Options:**
    
    - A. Profit Maximization (手数料・収益の最大化)
        
    - B. Fiduciary Duty as Code (真の受託者責任のコード化)
        
- **Decision:** **B. Fiduciary Duty as Code**
    
- **Reasoning:**
    
    - **Alignment is the Product:** AGI時代において、顧客は「機能」ではなく「自分の利益を100%代弁してくれること（Alignment）」に対価を払う。利益相反の排除を倫理規定（テキスト）ではなく、目的関数（数式）として実装する。
        
    - **Lifetime Optimization:** 短期的な金融商品の販売ではなく、ユーザーの人生設計（ライフプラン）全体の成功確率を最大化することを報酬系（Reward Model）に設定する。
        
    - **Defensive Moat:** 「SBIのAGIは、絶対に私を裏切らない」という数学的な保証こそが、他社のブラックボックスなAIに対する最強の競争優位性となる。
        

