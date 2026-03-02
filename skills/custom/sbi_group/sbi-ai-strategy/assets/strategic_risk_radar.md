# Strategic Risk Radar for AGI

AGIプロジェクトを脅かす5つのリスク領域と、その監視指標。

## 1. Regulatory Risk (規制)
*   **EU AI Act:** 欧州でのAI利用規制（高リスクAIへの分類）に抵触しないか。
*   **Copyright:** 生成AIの学習データに関する著作権訴訟の動向。
*   **Indicator:** 規制当局のパブリックコメント募集件数、主要な訴訟の判決。

## 2. Vendor Risk (依存)
*   **Lock-in:** 特定のLLM（OpenAI等）に依存しすぎていないか。API価格の急騰やサービス停止に耐えられるか。
*   **Data Leakage:** プロンプト経由で機密情報がベンダーに学習されていないか。
*   **Indicator:** APIコストのベンダー別比率、オープンモデルへの切り替え所要時間。

## 3. Technology Risk (技術)
*   **Hallucination:** AIの嘘により、金融事故（誤発注、不当融資）が発生するリスク。
*   **Obsolescence:** 現在の技術（Transformer）が、数年で陳腐化するリスク。
*   **Indicator:** RAG回答の正確性スコア、最新論文（ArXiv）の技術トレンドとの乖離度。

## 4. Security Risk (防衛)
*   **Injection:** プロンプトインジェクションによるAIの乗っ取り。
*   **Data Poisoning:** 学習データに悪意あるノイズを混入される攻撃。
*   **Indicator:** レッドチーム演習での突破成功率、セキュリティインシデント発生件数。

## 5. Ethical Risk (倫理)
*   **Bias:** 人種・性別による差別的な判断。
*   **Job Displacement:** AIによる大量解雇が社会問題化し、レピュテーションが毀損するリスク。
*   **Indicator:** 公平性監査（Fairness Audit）の結果、従業員エンゲージメントスコア。

