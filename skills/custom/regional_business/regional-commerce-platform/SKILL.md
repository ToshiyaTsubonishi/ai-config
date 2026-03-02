---
name: regional-commerce-platform
description: 近隣住民の購買意欲（ウィッシュリスト）を名寄せし、共同購入（Bulk Buy）による配送コスト削減や価格交渉を自動化するエージェント。
version: 2.0.0
author: SBI Orchestrator
---
# regional-commerce-platform (Local Group Buy)

## 1. Overview
「ご近所さん」の力を集結させ、賢く安く買い物をするためのプラットフォームスキルです。
物流の2024年問題（ドライバー不足）を解決するラストワンマイルの効率化と、地域コミュニティの再生を同時に実現します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 共同購入管理 | **Community Buy Orchestrator** | 住民の注文を取りまとめ、大口発注による割引を実現。 |
| 地域在庫・フードロス監視 | **Local Inventory Watcher** | スーパーの売れ残り情報をリアルタイムで配信し、廃棄を削減。 |

## 3. Workflow
1. **Wish**: 住民がアプリで「北海道の牡蠣が欲しい」と登録。
2.  **Aggregate**: `Community Buy Orchestrator` が近隣の注文を集約し、最低注文数（MOQ）を達成。
3.  **Deliver**: 地域の公民館やコンビニに一括配送し、個別に受け取り。

## 4. Operational Principles
*   **Trust**: 顔の見える関係（ご近所）をベースにした信頼設計。
*   **Eco**: 配送トラックの走行距離を減らし、CO2を削減する。
