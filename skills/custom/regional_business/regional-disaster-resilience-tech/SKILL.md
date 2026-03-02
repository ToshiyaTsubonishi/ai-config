---
name: regional-disaster-resilience-tech
description: 住民から提供された被災画像や衛星写真（SAR）、ドローン映像を解析し、建物の全壊・半壊などの「罹災判定」をAIで一次審査し、罹災証明書の発行を迅速化するエージェント。
version: 2.0.0
author: SBI Orchestrator
---
# regional-disaster-resilience-tech (Disaster Tech)

## 1. Overview
災害からの「復興速度」を劇的に高めるスキルです。
被災状況の把握から証明書の発行、そして支援金の給付までをデジタル完結させ、被災者が一日も早く日常を取り戻せるよう支援します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 罹災判定・被害調査 | **Damage Assessment AI** | 画像解析AIを用いて、家屋の損壊レベルを公平かつ高速に判定。 |
| 個別避難誘導 | **Hyper Local Alert Coordinator** | 一人ひとりの居場所に合わせた、最適な避難ルートをナビゲート。 |

## 3. Workflow
1. **Evacuate**: `Hyper Local Alert Coordinator` が、浸水想定区域にいる住民に個別の避難指示を送信。
2.  **Survey**: 被災後、ドローンや住民のスマホから画像を収集。
3.  **Judge**: `Damage Assessment AI` が全壊・半壊を判定し、データベースに登録。
4.  **Issue**: マイナンバーカードと連携し、罹災証明書をコンビニで発行可能にする。

## 4. Operational Principles
*   **Resilience**: 通信が途絶しても、オフラインでデータ収集できるアプリを提供する。
*   **Equity**: AIの判定基準を公開し、不服申し立てのプロセスも用意する。
