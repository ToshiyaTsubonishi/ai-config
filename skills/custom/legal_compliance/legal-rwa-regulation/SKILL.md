---
name: legal-rwa-regulation
description: 不動産や債権のトークン化（RWA/STO）に伴う、金商法および各国の規制への適合性を審査・保証するスキル。
version: 2.0.0
author: SBI Orchestrator
---
# legal-rwa-regulation (Token Law)

## 1. Overview
「コードが法律（Code is Law）」の世界と、現実世界の法律（Civil Law）の橋渡しをするスキルです。
セキュリティトークン（STO）が金融商品取引法などの規制に適合しているかを厳密にチェックし、適法なトークンエコノミーを実現します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 金商法・勧誘規制チェック | **FIEA Checker** | トークンの性質（一項・二項有価証券）を判定し、販売勧誘の適法性を審査。 |
| STOスキーム設計・適法性評価 | **RWA Legal Structurer** | 信託や匿名組合など、資産に応じた最適な法的スキームを構築。 |

## 3. Workflow
1. **Analyze**: トークンの設計（配当権、議決権）を確認。
2.  **Structure**: `RWA Legal Structurer` が、倒産隔離（Bankruptcy Remote）が機能するスキームを設計。
3.  **Check**: `FIEA Checker` が、ホワイトペーパーの記載内容が広告規制に違反していないか確認。

## 4. Operational Principles
*   **Global**: 日本だけでなく、販売対象国（米国、シンガポール等）の規制もクリアする。
*   **Update**: 頻繁に変わるWeb3関連法案を常にキャッチアップする。
