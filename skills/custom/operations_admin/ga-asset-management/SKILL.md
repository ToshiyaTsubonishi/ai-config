---
name: ga-asset-management
description: オフィス備品、IT機器、および固定資産の調達から廃棄までのライフサイクルを管理し、コスト最適化と不正防止を行うスキル。
version: 2.0.0
author: SBI Orchestrator
---
# ga-asset-management (Asset Master)

## 1. Overview
「モノ」の流れを可視化し、無駄な調達を防ぐとともに、資産の保全を図るスキルです。
IT資産管理（ITAM）とファシリティマネジメントを統合し、調達・利用・廃棄の全プロセスを最適化します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 在庫管理・棚卸し | **Inventory Auditor** | RFIDや画像認識を活用し、実地棚卸の工数を削減。 |
| 備品調達・購買最適化 | **Smart Procurement Agent** | 社内在庫の再利用を優先し、新規購入時は最適価格で発注。 |

## 3. Workflow
1. **Request**: 社員が必要な備品を申請。
2.  **Check**: `Smart Procurement Agent` が、遊休在庫がないか確認。なければAmazonビジネス等で価格比較。
3.  **Deploy**: 納品後、`Inventory Auditor` が資産タグを紐付け、台帳登録。
4.  **Dispose**: 耐用年数を迎えたら、データ消去とリサイクルを手配。

## 4. Operational Principles
*   **Sustainability**: 廃棄物を減らし、サーキュラーエコノミーに貢献する。
*   **Security**: 紛失・盗難を即座に検知する仕組みを持つ。
