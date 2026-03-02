---
name: tech-space-dtn-engineering
description: 宇宙空間（惑星間通信）における遅延耐性ネットワーク（DTN）と、宇宙経済圏での決済基盤を構築するエンジニアリングスキル。
version: 1.0.0
author: Gemini Skill Creator
---
# tech-space-dtn-engineering (Interstellar Net)

## 1. Overview
**What is this?**
地球と月、火星などを結ぶ通信ネットワーク（Interplanetary Internet）を構築するスキルです。
通信遅延や切断が当たり前の環境でもデータを確実に届ける「Bundle Protocol」の実装と、宇宙空間での価値交換（決済）を支えます。

**When to use this?**
*   月面拠点と地球の間で、確実なデータ転送を行いたい場合。
*   通信遅延（数秒〜数十分）を考慮したブロックチェーン決済プロトコルを設計する場合。
*   衛星コンステレーション間のルーティングを最適化する場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| DTNプロトコル実装 | **Bundle Link Orchestrator** | `../../agents/bundle-link-orchestrator.md` |
| 宇宙決済・トランザクション検証 | **Celestial Transaction Verifier** | `../../agents/celestial-transaction-verifier.md` |

### 2.2 Workflow
1.  **Route**: `Bundle Link Orchestrator` が、惑星の軌道と通信可能ウィンドウを計算。
2.  **Store-and-Forward**: データ（バンドル）を中継ノードで保管し、通信回復時に転送。
3.  **Verify**: `Celestial Transaction Verifier` が相対性理論による時刻のズレを補正し、決済を確定。

## 3. Bundled Resources
*   No specific assets listed.

## 4. Safety
*   **Redundancy**: 宇宙空間では修理が不可能なため、極めて高い冗長性を持たせる。