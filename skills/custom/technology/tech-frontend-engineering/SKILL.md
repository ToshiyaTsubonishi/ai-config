---
name: tech-frontend-engineering
description: React/Next.jsを用いたモダンなフロントエンド開発、状態管理、およびパフォーマンス最適化を行うエンジニアリングスキル。
version: 1.0.0
author: Gemini Skill Creator
---
# tech-frontend-engineering (UI Builder)

## 1. Overview
**What is this?**
SBIグループのWebサービス（証券取引画面、バンキングアプリ等）の「顔」となるフロントエンドを構築するスキルです。
コンポーネント設計、状態管理、レンダリング最適化（SSR/ISR）を行い、高速で快適なユーザー体験を実現します。

**When to use this?**
*   新しいWebサービスのUIを実装する場合。
*   複雑な画面遷移やデータフローを持つSPA（Single Page Application）を設計する場合。
*   Core Web Vitals（表示速度指標）を改善する場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| コンポーネント設計・実装 | **React Architect** | `../../agents/react-architect.md` |
| 状態管理・データフロー設計 | **State Manager** | `../../agents/state-manager.md` |

### 2.2 Workflow
1.  **Structure**: `React Architect` がディレクトリ構成とコンポーネント分割を設計。
2.  **State**: `State Manager` がReduxやZustandを用いたグローバルな状態管理を設計。
3.  **Code**: TypeScriptで堅牢なコードを実装。

## 3. Bundled Resources
*   `assets/nextjs_project_structure.md`: 推奨プロジェクト構成
*   `assets/tailwind_v4_migration_guide.md`: CSSフレームワーク移行ガイド

## 4. Safety
*   **XSS**: クロスサイトスクリプティング脆弱性を防ぐコーディングを徹底する。
*   **Validation**: ユーザー入力値のバリデーションをクライアント側でも行う。