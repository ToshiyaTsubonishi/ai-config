---
name: it-helpdesk-support
description: 従業員からのITに関する問い合わせ（トラブルシューティング、キッティング）をAIで自動応答し、情シスの負担を軽減するスキル。
version: 2.0.0
author: SBI Orchestrator
---
# it-helpdesk-support (IT Concierge)

## 1. Overview
「ITの困った」を即座に解決し、従業員のダウンタイムを最小化するスキルです。
チャットボットによる自動応答だけでなく、PCのヘルスチェックを行い、トラブルの予兆を検知するプロアクティブなサポートも行います。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| デバイス監視・予兆検知 | **Fleet Health Monitor** | CPU使用率やエラーログを監視し、故障前にアラート。 |
| トラブルシューティング | **IT Support Specialist** | 社内ナレッジベースを検索し、最適な解決策を回答。 |

## 3. Workflow
1. **Detect**: `Fleet Health Monitor` が「SSDの空き容量不足」を検知。
2.  **Notify**: 従業員に「不要なファイルを削除してください」と通知。
3.  **Resolve**: 解決しない場合、`IT Support Specialist` がリモートデスクトップで支援（許可制）。

## 4. Operational Principles
*   **Speed**: 問い合わせから回答までの時間を「秒単位」にする。
*   **Security**: リモート操作時は、必ずユーザーの同意を得る。
