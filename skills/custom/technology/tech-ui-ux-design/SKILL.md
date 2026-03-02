---
name: tech-ui-ux-design
description: デザインシステム構築とデータ駆動のUX改善を統合し、最高品質の金融インターフェースを提供するデザイン戦略スキル。
version: 1.0.0
author: Gemini Skill Creator
---
# tech-ui-ux-design (Design System)

## 1. Overview
**What is this?**
SBIグループ共通のデザイン言語（Design System）を定義・運用し、一貫性のあるブランド体験と、使いやすいUIを提供するスキルです。
Figmaとコード（Reactコンポーネント）を同期させ、デザイナーとエンジニアの協業を加速します。

**When to use this?**
*   新しいサービスのUIデザインを行う場合。
*   既存アプリの使い勝手（ユーザビリティ）を改善する場合。
*   アクセシビリティ対応（WCAG準拠）や、ダークモード対応を行う場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| デザインシステム管理・Component設計 | **Design System Maintainer** | `../../agents/design-system-maintainer.md` |
| UXリサーチ・ユーザビリティテスト | **UX Research Analyst** | `../../agents/ux-research-analyst.md` |

### 2.2 Workflow
1.  **Analyze**: `UX Research Analyst` がユーザー行動（ヒートマップ、離脱率）を分析し、課題を特定。
2.  **Design**: `Design System Maintainer` がデザインシステムに基づき、修正案（ワイヤーフレーム）を作成。
3.  **Prototype**: Figmaやコードでプロトタイプを作成し、テスト。
4.  **Implement**: エンジニア（`tech-frontend-engineering`）に引き継ぎ。

## 3. Bundled Resources
*   `assets/agi_visual_identity.md`: AGI時代のビジュアルアイデンティティ定義
*   `references/figma_design_guidelines.md`: Figma運用ガイドライン

## 4. Safety
*   **Accessibility**: 色覚多様性やスクリーンリーダーへの配慮を必須とする。
*   **Dark Patterns**: ユーザーを欺くようなUI（ダークパターン）は絶対に使用しない。