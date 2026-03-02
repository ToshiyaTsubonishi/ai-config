---
name: sbi-facility-manager
description: オフィスの清掃、警備、設備の維持管理（FM）を統括し、安全で快適なワークプレイスを提供するスキル。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-facility-manager (Office OS)

## 1. Overview
物理的な執務環境を「経営インフラ」として最適化するスキルです。
IoTデータとロボットを活用し、清掃・警備・保守の効率を最大化するとともに、従業員の健康と安全（Wellness & Safety）を守ります。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 清掃・衛生管理 | **Cleaning Scheduler** | 人流データに基づき、汚れやすい場所を重点的に清掃指示。 |
| オフィス安全点検 | **Office Safety Guard** | 法定点検や設備の不具合（電球切れ等）を自動管理。 |

## 3. Workflow
1. **Sense**: 人感センサーで会議室やカフェスペースの利用状況を把握。
2. **Dispatch**: `Cleaning Scheduler` が清掃ロボットやスタッフに動的ルートを提示。
3. **Audit**: `Office Safety Guard` が、消火器の期限や避難通路の障害物を定期チェック。
4. **Respond**: 社員からの「冷房が寒い」等のリクエストに即座に対応（`facility-concierge` 連携）。

## 4. Operational Principles
* **Cost Efficiency**: 無駄な清掃や過剰な照明をカットし、運用コストを削減。
* **Employee Experience**: オフィスの不快指数をゼロにする。
