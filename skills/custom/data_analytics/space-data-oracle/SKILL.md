---
name: space-data-oracle
description: 衛星データ（位置情報、観測データ）をブロックチェーン上のスマートコントラクトに信頼できる形で提供するオラクルスキル。
version: 1.0.0
author: Gemini Skill Creator
---
# space-data-oracle (Space Bridge)

## 1. Overview
**What is this?**
「宇宙で起きたこと」をブロックチェーン上の金融取引のトリガーにするためのスキルです。
複数の衛星や地上局からのデータをクロスチェックし、データの真正性を担保した上で、オンチェーンに書き込みます。

**When to use this?**
*   「衛星が軌道に到達したら保険金を支払う」スマートコントラクトを動かす場合。
*   月面での資源採掘量を証明し、トークンを発行する場合。
*   デブリ除去の実績を証明する場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| 天体・衛星データ統合 | **Celestial Data Aggregator** | `../../agents/celestial-data-aggregator.md` |
| 宇宙事象の検証（Proof of Space） | **Orbital Trust Verifier** | `../../agents/orbital-trust-verifier.md` |

### 2.2 Workflow
1.  **Observe**: `Celestial Data Aggregator` がJAXAやNASAのAPI、および民間衛星のデータを収集。
2.  **Verify**: `Orbital Trust Verifier` が、複数のソースが一致しているか確認（コンセンサス）。
3.  **Commit**: 検証されたデータをChainlink等のオラクルネットワーク経由で送信。

## 3. Bundled Resources
*   No specific assets listed.

## 4. Safety
*   **Sybil Attack**: 偽の衛星データによる攻撃を防ぐため、信頼できるノードのみを採用する。