# スマートコントラクト監査チェックリスト (Audit Checklist)

## 1. 基本的な脆弱性 (Basic Vulnerabilities)
- [ ] **Reentrancy:** 外部呼び出しの前に状態変数を更新しているか？ `nonReentrant` 修飾子を使用しているか？
- [ ] **Integer Overflow/Underflow:** Solidity 0.8.0以上を使用しているか？
- [ ] **Access Control:** `onlyOwner` や特定のロール制限が重要な関数に適切に適用されているか？
- [ ] **Unchecked Return Values:** 低レベルの `call` の戻り値をチェックしているか？
- [ ] **Denial of Service (DoS):** ループ処理がガスリミットを超える可能性はないか？（外部ユーザーが配列の長さを操作できる場合など）
- [ ] **Timestamp Dependence:** `block.timestamp` を重要なロジック（乱数生成等）に使用していないか？

## 2. ビジネスロジック・仕様 (Business Logic)
- [ ] **Tokenomics:** トークンの発行上限（Cap）、焼却（Burn）、ミント（Mint）のロジックは仕様通りか？
- [ ] **Fee Calculation:** 手数料の計算で精度落ち（Rounding Error）が発生していないか？ 常に分子を先に掛けているか？
- [ ] **Front-running:** トランザクションの順序によって不当な利益を得られる隙はないか？

## 3. オラクル・外部連携 (Oracle & Integration)
- [ ] **Price Manipulation:** AMMのスポット価格を直接使用していないか？（TWAPまたはChainlinkを使用すべき）
- [ ] **Stale Data:** オラクルからのデータが古くないかチェックしているか？
- [ ] **Trusted Setup:** 外部コントラクトのアドレスは信頼できるものか？ 変更可能か？

## 4. アップグレード・管理 (Upgradability & Admin)
- [ ] **Storage Layout:** アップグレード時にストレージスロットが衝突しないように `__gap` 変数を確保しているか？
- [ ] **Initializers:** プロキシコントラクトの `initialize` 関数は一度しか呼べないように保護されているか？
- [ ] **Centralization Risk:** 管理者権限（Admin Key）が強すぎないか？ TimelockやMulti-Sigを使用しているか？

## 5. ガス最適化 (Gas Optimization)
- [ ] **Storage vs Memory:** データを適切にメモリにキャッシュしているか？
- [ ] **Loop Optimization:** ループ内でのストレージ書き込みを避けているか？
- [ ] **Data Types:** `uint256` を使用するのが基本（EVMは32バイトワードのため）。構造体パッキング（`uint128` + `uint128`）は必要な場合のみ行う。
