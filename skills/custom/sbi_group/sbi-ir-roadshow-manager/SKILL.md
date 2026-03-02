---
name: sbi-ir-roadshow-manager
description: 機関投資家向けの説明会（ロードショー）のロジ手配、資料作成、および投資家ターゲティングを支援するIRスキル。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-ir-roadshow-manager (Roadshow Master)

## 1. Overview
短期間で世界中の投資家を回るロードショーを、物理的にも戦略的にも成功させるスキルです。
「誰に会うべきか（ターゲティング）」と「何を話すべきか（ストーリー）」を最適化し、オファリングの成功率を高めます。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| エクイティ・ストーリー構築 | **Equity Story Teller** | 投資家の属性（グロース/バリュー）に合わせたプレゼン資料を作成。 |
| 投資家ターゲティング | **Investor Matching Bot** | 保有銘柄の傾向から、自社株を買ってくれそうなファンドをリストアップ。 |

## 3. Workflow
1. **Target**: `Investor Matching Bot` が、「日本のテック株をオーバーウェイトしている海外投資家」を抽出。
2.  **Story**: `Equity Story Teller` が、その投資家向けのピッチデックを作成。
3.  **Logistics**: `Roadshow Logistics Bot`（`sbi-event-director` 連携）が、NY・ロンドン・香港を回る旅程を組む。
4.  **Feedback**: 面談後の反応を記録し、価格決定（プライシング）の参考にする。

## 4. Operational Principles
*   **Efficiency**: 経営陣の体力を消耗させないよう、移動時間を最小化する。
*   **Compliance**: インサイダー情報の管理（Wall Crossing）を徹底する。
