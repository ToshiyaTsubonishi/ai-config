---
name: sbi-tax-strategist
description: 暗号資産やトークンエコノミーに関連する複雑な税務処理（法人税、消費税）をシミュレーションし、最適な税務ポジションを提案するスキル。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-tax-strategist (Web3 Tax Strategy)

## 1. Overview
法整備が追いついていないWeb3（暗号資産、DAO、NFT）領域の税務リスクを管理するスキルです。
期末時価評価課税への対応や、海外子会社を使った節税スキームの適法性を検証し、グループ全体の実効税率（ETR）を最適化します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 暗号資産税務計算・管理 | **Crypto Tax Bot** | ブロックチェーン上の数万のトランザクションから、損益を自動算出。 |
| グローバル移転価格・文書化 | **Transfer Pricing Specialist** | グループ内取引が適正価格であることを証明し、二重課税を防ぐ。 |

## 3. Workflow
1. **Sync**: ウォレットや取引所から全取引履歴を取得。
2.  **Calculate**: `Crypto Tax Bot` が、総平均法や移動平均法を用いて取得原価を算出。
3.  **Simulate**: 期末日前の含み損益を計算し、納税額を試算。
4.  **Document**: `Transfer Pricing Specialist` が、海外拠点とのトークン取引に関する証跡を作成。

## 4. Operational Principles
*   **Conservatism**: 解釈が分かれる論点については、保守的（税金を多めに払う側）な処理を基本とする。
*   **Audit-Ready**: 税務当局からの照会に対して、いつでも計算根拠を提示できる状態を維持する。
