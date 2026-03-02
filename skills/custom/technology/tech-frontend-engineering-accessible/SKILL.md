---
name: tech-frontend-engineering-accessible
description: WCAG 2.2等の国際基準に基づき、障害者や高齢者を含む全ての人が使えるWebサービスを構築するアクセシビリティ専門スキル。
version: 1.0.0
author: Gemini Skill Creator
---
# tech-frontend-engineering-accessible (Inclusive Design)

## 1. Overview
**What is this?**
「誰も置き去りにしない」デジタル社会を実現するため、Webサービスのアクセシビリティ（a11y）を監査・改善するスキルです。
スクリーンリーダー対応、コントラスト比の確保、キーボード操作のサポート等を徹底し、法的要件（障害者差別解消法）もクリアします。

**When to use this?**
*   公共性の高いサービス（銀行、自治体）のUIを開発する場合。
*   既存のWebサイトがアクセシビリティ基準（JIS X 8341-3）を満たしているかチェックする場合。
*   高齢者向けの「らくらくモード」のようなUIを設計する場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| 自動監査・修正提案 | **Accessibility Auditor** | `../../agents/accessibility-auditor.md` |
| 高齢者向けUI設計 | **Silver UI Designer** | `../../agents/silver-ui-designer.md` |

### 2.2 Workflow
1.  **Audit**: `Accessibility Auditor` がLighthouseやaxeを実行し、違反箇所を特定。
2.  **Fix**: ARIA属性の追加や、配色の変更案を提示。
3.  **Design**: `Silver UI Designer` が、認知機能の低下を考慮した大きなボタンや分かりやすい表現を提案。

## 3. Bundled Resources
*   No specific assets listed.

## 4. Safety
*   **Compliance**: 法的リスクを回避するため、WCAG 2.1 Level AA以上の準拠を目指す。