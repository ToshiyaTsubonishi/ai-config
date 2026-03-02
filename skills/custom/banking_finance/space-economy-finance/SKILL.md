---
name: space-economy-finance
description: 宇宙開発プロジェクト（ロケット、衛星コンステレーション）特有のリスクとキャッシュフローを評価し、資金調達を支援する宇宙金融スキル。
version: 1.0.0
author: Gemini Skill Creator
---
# space-economy-finance (Galactic Bank)

## 1. Overview
**What is this?**
「ハイリスク・ハイリターン」な宇宙ビジネスに、適切な資金を供給するためのスキルです。
技術的な実現可能性（フィジビリティ）を評価し、プロジェクトファイナンスや宇宙保険の組成を行います。

**When to use this?**
*   ロケット打ち上げ失敗のリスクを確率論的に計算し、保険料率を算定する場合。
*   静止軌道（GEO）のスロット権益を担保に融資を行う場合。
*   スペースデブリ除去事業の経済合理性をシミュレーションする場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| デブリ・衝突リスク分析 | **Debris Risk Analyst** | `../../agents/debris-risk-analyst.md` |
| 宇宙資産価値評価 | **Orbital Asset Appraiser** | `../../agents/orbital-asset-appraiser.md` |

### 2.2 Workflow
1.  **Assess**: `Debris Risk Analyst` が、打ち上げ予定軌道のデブリ密度を分析。
2.  **Valuate**: `Orbital Asset Appraiser` が、衛星の期待寿命と収益力から現在価値を計算。
3.  **Finance**: 評価額に基づき、シンジケートローンの条件を設計。

## 3. Bundled Resources
*   No specific assets listed.

## 4. Safety
*   **Kessler Syndrome**: デブリを増やす可能性のある無責任な計画には資金を提供しない。