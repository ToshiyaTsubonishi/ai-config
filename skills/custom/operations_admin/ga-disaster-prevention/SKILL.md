---
name: ga-disaster-prevention
description: 地震、火災、パンデミックなどの災害発生時に、従業員の安否確認と事業継続（BCP）の初動対応を自動指揮するスキル。
version: 2.0.0
author: SBI Orchestrator
---
# ga-disaster-prevention (Crisis Response)

## 1. Overview
「想定外」を想定内にする、有事の際の自動司令塔スキルです。
人間の判断力が低下する緊急時において、予め定義されたプロトコル（BCP）に従って冷静かつ迅速に行動を開始します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 初動指揮・安否確認 | **BCP Orchestrator Bot** | 全従業員への連絡と、回答状況のリアルタイム集計。 |
| 災害情報収集・リスク検知 | **Hybrid Hazard Monitor** | 気象庁APIやSNSから、正確な被害状況を把握。 |

## 3. Workflow
1. **Trigger**: `Hybrid Hazard Monitor` が震度5強以上の地震を検知。
2.  **Alert**: `BCP Orchestrator Bot` がSlack/メール/電話で安否確認を一斉送信。
3.  **Command**: 対策本部（CEO等）へ被害予測レポートを送信し、事業継続判断を仰ぐ。
4.  **Support**: 帰宅困難者に対し、備蓄品の配布や宿泊場所の案内を行う。

## 4. Operational Principles
*   **Speed**: 検知から発報までを数秒以内に行う。
*   **Redundancy**: メインシステムがダウンしても稼働する、独立した通信経路を確保。
