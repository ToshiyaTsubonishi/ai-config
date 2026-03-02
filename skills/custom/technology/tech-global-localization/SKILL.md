---
name: tech-global-localization
description: Webサービスやコンテンツを、世界各国の言語、文化、法規制に合わせて最適化（ローカライズ/カルチャライズ）するスキル。
version: 1.0.0
author: Gemini Skill Creator
---
# tech-global-localization (Global Reach)

## 1. Overview
**What is this?**
単なる翻訳ではなく、現地の商習慣、通貨、日付フォーマット、さらには宗教的・文化的なタブーを考慮して、サービスを現地化するスキルです。
SBIグループのグローバル展開（アジア、中東、アフリカ）を技術面から支えます。

**When to use this?**
*   日本で作ったアプリをベトナムやサウジアラビアで展開する場合。
*   i18n（国際化）対応の基盤（ライブラリ選定、翻訳フロー）を構築する場合。
*   現地の法規制（GDPR等）に合わせたUI変更（Cookie同意バナー等）を行う場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| コンテンツのカルチャライズ | **Localized Content Producer** | `../../agents/localized-content-producer.md` |
| i18nエンジニアリング | **React Architect** | `../../agents/react-architect.md` (Shared) |

### 2.2 Workflow
1.  **Extract**: UI上のテキストを抽出し、翻訳管理システムに連携。
2.  **Translate**: `Localized Content Producer` が、直訳ではなく「意訳」を行う。
3.  **Adapt**: 通貨記号（¥/$）、日付順序、RTL（右から左へ書く言語）対応を実装。

## 3. Bundled Resources
*   `assets/nextjs_i18n_pattern.tsx`: Next.jsでの国際化実装パターン

## 4. Safety
*   **Cultural Sensitivity**: 政治的・宗教的に敏感な話題やデザインを避ける。