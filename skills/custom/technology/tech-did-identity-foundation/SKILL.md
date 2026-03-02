---
name: tech-did-identity-foundation
description: W3C標準の分散型ID（DID）とVerifiable Credentials（VC）を用いた、次世代のデジタルアイデンティティ基盤を構築するスキル。
version: 1.0.0
author: Gemini Skill Creator
---
# tech-did-identity-foundation (Self-Sovereign Identity)

## 1. Overview
**What is this?**
ユーザーが自分の個人情報を自分で管理する「自己主権型アイデンティティ（SSI）」を実現するスキルです。
特定の企業（GAFA）に依存せず、ブロックチェーン技術を用いて、学歴、職歴、本人確認情報（KYC）を安全に証明します。

**When to use this?**
*   サービス間での面倒なID登録・パスワード管理をなくしたい場合（パスワードレス）。
*   「20歳以上であること」だけを証明し、生年月日は隠す（最小開示）場合。
*   社員証や資格証明書をデジタル化し、スマホで持ち運べるようにする場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| 証明書発行・署名 | **Credential Issuer Bot** | `../../agents/credential-issuer-bot.md` |
| ゼロ知識証明・開示制御 | **Selective Disclosure Proxy** | `../../agents/selective-disclosure-proxy.md` |

### 2.2 Workflow
1.  **Issue**: `Credential Issuer Bot` が、大学や銀行の署名付きでVC（Verifiable Credential）を発行。
2.  **Hold**: ユーザーは自身のウォレットにVCを保管。
3.  **Prove**: `Selective Disclosure Proxy` が、サービスが必要とする情報だけを選択して提示（ゼロ知識証明）。

## 3. Bundled Resources
*   No specific assets listed.

## 4. Safety
*   **Revocation**: 秘密鍵の紛失時や、証明書の失効（退職など）に対応できる仕組みを用意する。
*   **Interoperability**: 国際標準（W3C DID）に準拠し、異なるシステム間での相互運用性を確保する。