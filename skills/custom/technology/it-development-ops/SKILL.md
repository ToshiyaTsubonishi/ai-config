---
name: it-development-ops
description: アジャイル開発プロセスを加速させるCI/CDパイプラインの構築、コードレビューの自動化、およびリリース管理を行うスキル。
version: 2.0.0
author: SBI Orchestrator
---
# it-development-ops (DevOps Master)

## 1. Overview
金融システムに求められる「堅牢性」と、Webサービスに求められる「スピード」を両立させるスキルです。
開発（Dev）と運用（Ops）にセキュリティ（Sec）とコンプライアンスを統合し、安全かつ高速なリリースサイクルを実現します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| コンプライアンス・証跡記録 | **Compliance Automation Agent** | 誰がいつ承認し、何をデプロイしたかを自動記録し、監査に対応。 |
| CI/CDパイプライン管理 | **DevSecOps Pipeline Master** | ビルド、テスト、セキュリティスキャン、デプロイを一気通貫で自動化。 |

## 3. Workflow
1. **Commit**: エンジニアがコードをリポジトリにプッシュ。
2.  **Scan**: `DevSecOps Pipeline Master` が静的解析（SAST）と依存関係チェックを実行。
3.  **Approve**: テスト通過後、`Compliance Automation Agent` が承認フロー（プルリクエスト）を監視。
4.  **Deploy**: 本番環境へのリリースと同時に、変更履歴を監査ログに記録。

## 4. Operational Principles
*   **Automation**: 手動オペレーションを極限まで減らし、ヒューマンエラーを防ぐ。
*   **Auditability**: すべての変更は追跡可能でなければならない。
