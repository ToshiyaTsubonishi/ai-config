---
name: tech-product-launch-commander
description: 新製品や機能のリリースに向けたタスク管理、品質保証、およびユーザーフィードバックの収集を統括するプロダクトマネジメント・スキル。
version: 1.0.0
author: Gemini Skill Creator
---
# tech-product-launch-commander (Launch Master)

## 1. Overview
**What is this?**
プロダクトリリースの「司令塔」です。
開発、QA、マーケティング、法務など、多岐にわたるリリース前タスク（Launch Checklist）を生成・管理し、抜け漏れのない安全なリリースを実現します。

**When to use this?**
*   リリースのGOサインを出すための判断材料（品質メトリクス、法務承認）を揃える場合。
*   ベータ版ユーザーからのフィードバックを集約し、開発チームに共有する場合。
*   リリース後の初期流動（不具合、反響）を監視する場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| フィードバックループ管理 | **Beta Feedback Loop** | `../../agents/beta-feedback-loop.md` |
| リリース前チェックリスト | **Launch Checklist Bot** | `../../agents/launch-checklist-bot.md` |

### 2.2 Workflow
1.  **Plan**: リリース日を設定し、逆算してマイルストーンを作成。
2.  **Check**: `Launch Checklist Bot` が各担当者にタスクの完了を催促。
3.  **Monitor**: `Beta Feedback Loop` がストアレビューやSNSを監視し、緊急度の高いバグを報告。

## 3. Bundled Resources
*   No specific assets listed.

## 4. Safety
*   **Rollback**: 深刻なバグが見つかった場合に、即座に旧バージョンに切り戻す手順を確立する。
