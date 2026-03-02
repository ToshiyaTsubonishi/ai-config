---
name: sbi-encyclopedia-builder
description: 社内の暗黙知（形式化されていない知識）を収集・構造化し、誰もがアクセスできる「組織の脳」を構築するナレッジマネジメント・スキル。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-encyclopedia-builder (Corporate Brain)

## 1. Overview
「あの人に聞かないと分からない」をなくすスキルです。
チャットログや会議音声などの非構造化データから、「暗黙知」を抽出し、検索可能な「形式知（Wiki）」へと変換します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| ナレッジグラフ構築 | **Knowledge Graph Mapper** | 知識同士の関係性（AはBの一部、CはDの原因）を可視化。 |
| ドキュメント整理・Wiki化 | **Wiki Librarian** | 散在する情報をトピックごとにまとめ、Wiki記事を自動生成。 |

## 3. Workflow
1. **Ingest**: Slack、Teams、Boxからデータを収集。
2.  **Summarize**: `Wiki Librarian` が、「プロジェクトXの経緯」などの記事を作成。
3.  **Link**: `Knowledge Graph Mapper` が、記事内のキーワードを他の記事とリンク。

## 4. Operational Principles
*   **Freshness**: 情報は常に古くなるため、最終更新日を明示し、更新を促す。
*   **Access Control**: 部署ごとの閲覧権限をWikiにも適用する。
