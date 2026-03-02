---
name: community-dao-governance
description: 分散型自律組織（DAO）の憲法策定、議案投票システム、およびコミュニティの感情分析を統合管理するガバナンススキル。
version: 2.0.0
author: SBI Orchestrator
---
# community-dao-governance (DAO Operating System)

## 1. Overview
「新産業Creator」を目指すSBIグループにおいて、分散型の意思決定モデルを実装・管理するためのスキルです。
トークノミクスと連動した公平なガバナンスを構築し、コミュニティの力を最大化します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| ガバナンス議案審査・策定 | **DAO Proposal Reviewer** | 提案がDAO憲法や法的基準に合致しているか自動評価。 |
| コミュニティ監視・調整 | **Sentiment Moderator Bot** | Discord等のチャネルを監視し、議論の健全性を保つ介入を行う。 |

## 3. Workflow
1. **Listen**: `market-sentiment-tracker` 連携によりコミュニティの熱量を確認。
2. **Review**: 提出された議案に対し、`legal-opinion-bot` と連携して適法性を確認。
3. **Execute**: 投票結果に基づき、スマートコントラクト経由で資金移動や設定変更を自動執行。

## 4. Operational Principles
* **Transparency**: 意思決定プロセスの完全な透明化。
* **Fairness**: 一部のクジラ（大口保有者）による支配を防ぐための仕組み作り。
