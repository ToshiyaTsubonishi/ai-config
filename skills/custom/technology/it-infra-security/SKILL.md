---
name: it-infra-security
description: ゼロトラスト・アーキテクチャに基づき、社内ネットワーク、クラウド、およびエンドポイントのセキュリティを統合防御するスキル。
version: 2.0.0
author: SBI Orchestrator
---
# it-infra-security (Zero Trust Guard)

## 1. Overview
「社内ネットワークなら安全」という神話を捨て、すべてのアクセスを疑い、検証するスキルです。
ID、デバイス、振る舞いの3要素で認証を行い、マルウェアの侵入や内部不正を防ぎます。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 脅威検知・リアルタイム監視 | **AI Safety Monitor** | ネットワークトラフィックやログを解析し、攻撃の予兆を検知。 |
| 侵入テスト・脆弱性診断 | **Red Team Hacker** | 攻撃者の視点でシステムを攻撃し、弱点を洗い出す。 |
| アクセス制御・認証 | **Zero Trust Gatekeeper** | 「誰が」「どの端末で」「どこから」アクセスしているかを厳密に検証。 |

## 3. Workflow
1. **Access**: ユーザーが社内システムにアクセス。
2. **Verify**: `Zero Trust Gatekeeper` が、多要素認証（MFA）とデバイス健全性をチェック。
3.  **Detect**: `AI Safety Monitor` が、普段と異なる大量データ送信を検知し、セッションを遮断。
4.  **Harden**: `Red Team Hacker` が定期的に脆弱性を突き、防御策を強化。

## 4. Operational Principles
*   **Assume Breach**: 「侵入されている」ことを前提に、被害を最小化する設計（マイクロセグメンテーション）を行う。
*   **Automation**: 攻撃検知から遮断までの対応を自動化（SOAR）する。
