---
name: tech-mobile-engineering
description: iOS/Androidネイティブアプリのセキュリティ、パフォーマンス、および審査通過率を最大化するモバイル開発スキル。
version: 1.0.0
author: Gemini Skill Creator
---
# tech-mobile-engineering (App Master)

## 1. Overview
**What is this?**
Swift/Kotlinによるネイティブアプリ開発において、金融機関に求められる高度なセキュリティ（難読化、改竄検知）と、スムーズなUIを両立させるスキルです。
App Store/Google Playの審査ガイドラインを熟知し、リジェクト（審査落ち）を防ぎます。

**When to use this?**
*   銀行アプリに生体認証（FaceID/TouchID）を組み込む場合。
*   アプリがRoot化/脱獄された端末で起動しないよう、検知ロジックを入れる場合。
*   アプリストアへの申請用メタデータやスクリーンショットを準備する場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| ストア審査対策・リリース管理 | **App Store Specialist** | `../../agents/app-store-specialist.md` |
| モバイルセキュリティ実装 | **Mobile Security Guard** | `../../agents/mobile-security-guard.md` |

### 2.2 Workflow
1.  **Code**: セキュアなコーディング規約に基づいて実装。
2.  **Harden**: `Mobile Security Guard` がコード難読化とSSL Pinningを適用。
3.  **Review**: `App Store Specialist` が最新の審査ガイドラインと照らし合わせ、リジェクト要因を排除。

## 3. Bundled Resources
*   `scripts/example_script.py`: 自動ビルドスクリプト

## 4. Safety
*   **Data Leak**: クリップボードやログに機微情報（パスワード等）を残さない。