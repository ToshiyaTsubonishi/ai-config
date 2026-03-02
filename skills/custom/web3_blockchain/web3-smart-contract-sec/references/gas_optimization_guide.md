# ガス最適化ガイド (Gas Optimization Guide)

EVM (Ethereum Virtual Machine) における実行コスト（Gas）を削減するためのテクニック集。

## 1. ストレージ操作の削減 (SSTORE/SLOAD)
最もコストが高い操作であるストレージへの読み書きを減らす。

*   **Bad:**
    ```solidity
    for (uint i = 0; i < array.length; i++) {
        total += array[i]; // ループごとにSSTOREが発生する可能性
    }
    balance = total;
    ```
*   **Good:**
    ```solidity
    uint256 _total = total; // SLOAD (1回)
    for (uint i = 0; i < array.length; i++) {
        _total += array[i]; // メモリ上で計算
    }
    total = _total; // SSTORE (1回)
    ```

## 2. 変数のパッキング (Variable Packing)
1つのスロット（32バイト）に複数の変数を詰め込む。

*   **Bad:** (2スロット消費)
    ```solidity
    uint128 a;
    uint256 b;
    uint128 c;
    ```
*   **Good:** (2スロット消費 - aとcが1スロットに収まる)
    ```solidity
    uint128 a;
    uint128 c;
    uint256 b;
    ```

## 3. Calldataの使用
外部関数（external）の引数で、変更しない配列や文字列は `memory` ではなく `calldata` を指定する。

*   **Bad:** `function process(uint[] memory data) external`
*   **Good:** `function process(uint[] calldata data) external`

## 4. エラー文字列の短縮 / Custom Error
長いrequire文字列はデプロイコストと実行コストを増やす。Solidity 0.8.4以降の `error` 定義を使用する。

*   **Bad:** `require(balance >= amount, "Insufficient balance for transfer");`
*   **Good:**
    ```solidity
    error InsufficientBalance();
    if (balance < amount) revert InsufficientBalance();
    ```

## 5. 定数とImmutable
コンパイル時に値が決まる変数は `constant` または `immutable` を使用する。これらはストレージではなくバイトコードに埋め込まれるため、大幅に安い。

*   `uint256 public constant MAX_SUPPLY = 1000000;`
*   `address public immutable OWNER;`
