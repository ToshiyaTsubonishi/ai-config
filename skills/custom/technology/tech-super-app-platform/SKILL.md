---
name: tech-super-app-platform
description: 金融・非金融のあらゆるサービスを統合する「スーパーアプリ」の共通基盤（ID、決済、ミニアプリSDK）を提供するプラットフォームスキル。
version: 1.0.0
author: Gemini Skill Creator
---
# tech-super-app-platform (Super App Core)

## 1. Overview
**What is this?**
「一つのアプリで生活の全てが完結する」スーパーアプリを実現するための基盤技術スキルです。
ID管理（OpenID Connect）、決済ゲートウェイ、そしてサードパーティがミニアプリを開発するためのSDKを提供します。

**When to use this?**
*   共通ID（SBI ID）を用いたシングルサインオン（SSO）を実装する場合。
*   ミニアプリの開発者向けポータルやドキュメントを整備する場合。
*   アプリ内の決済機能を、銀行APIやクレジットカード決済と接続する場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| ID・認証基盤管理 | **Identity Orchestrator SBI** | `../../agents/identity-orchestrator-sbi.md` |
| ミニアプリSDK・エコシステム | **Mini App SDK Manager** | `../../agents/mini-app-sdk-manager.md` |

### 2.2 Workflow
1.  **Auth**: `Identity Orchestrator SBI` が、生体認証（FIDO）を用いたセキュアなログインを提供。
2.  **Dev**: パートナー企業がSDKを使ってミニアプリを開発。
3.  **Review**: `Mini App SDK Manager` がセキュリティ審査を行い、ストアに公開。

## 3. Bundled Resources
*   No specific assets listed.

## 4. Safety
*   **Sandboxing**: ミニアプリが悪意ある挙動をしないよう、WebViewの権限を制限する。
