---
name: tech-it-digital-transformation
description: レガシーシステムのモダナイズ（刷新）と、内製化組織の立ち上げを支援する、IT戦略の実行スキル。
version: 1.0.0
author: Gemini Skill Creator
---
# tech-it-digital-transformation (Legacy to Cloud)

## 1. Overview
**What is this?**
「2025年の崖」を克服するため、COBOLやオンプレミスに残るレガシー資産を、クラウドネイティブな環境へ移行するスキルです。
単なるシステム移行だけでなく、ベンダー丸投げ体質からの脱却（内製化）を強力に推進します。

**When to use this?**
*   メインフレーム上の勘定系システムを、オープン系サーバーへ移行する場合。
*   社内のITエンジニアを採用・育成し、アジャイル開発チームを組成する場合。
*   技術的負債（Technical Debt）を可視化し、返済計画を立てる場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| 内製化支援・チームビルディング | **Internalization Catalyst** | `../../agents/internalization-catalyst.md` |
| 技術的負債診断・移行計画 | **Legacy Debt Auditor** | `../../agents/legacy-debt-auditor.md` |

### 2.2 Workflow
1.  **Audit**: `Legacy Debt Auditor` がソースコードを解析し、負債の深刻度をスコアリング。
2.  **Plan**: マイグレーションの優先順位を決定（Strangler Figパターン等の適用）。
3.  **Build**: `Internalization Catalyst` が、社員とペアプログラミングを行い、スキル移転を進める。

## 3. Bundled Resources
*   `references/devops_standard_guideline.md`: DevOps標準ガイドライン
*   `references/zero_trust_requirements.md`: ゼロトラスト要件定義書

## 4. Safety
*   **Business Continuity**: 移行中のシステム停止を最小限に抑える。