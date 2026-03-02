---
name: sustainability-esg-strategy
description: 気候変動対策（脱炭素）や人的資本経営などのESG課題を経営戦略に統合し、非財務情報の開示を支援するサステナビリティスキル。
version: 1.0.0
author: Gemini Skill Creator
---
# sustainability-esg-strategy (ESG Compass)

## 1. Overview
**What is this?**
ESG（環境・社会・ガバナンス）への取り組みを、単なる「社会貢献」から「企業価値向上」の手段へと変えるスキルです。
温室効果ガス（GHG）排出量の算定や、人的資本データの開示（ISO 30414）を自動化し、投資家からの評価を高めます。

**When to use this?**
*   Scope 1, 2, 3のCO2排出量を算定し、SBTi（科学的根拠に基づく目標）を申請する場合。
*   統合報告書やサステナビリティレポートを作成する場合。
*   AIの電力消費を削減する「Green AI」施策を導入する場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| カーボンフットプリント算定 | **Carbon Footprint Analyst** | `../../agents/carbon-footprint-analyst.md` |
| ESG開示・レポーティング | **ESG Disclosure Expert** | `../../agents/esg-disclosure-expert.md` |
| AI省電力化 | **Green AI Optimizer** | `../../agents/green-ai-optimizer.md` |

### 2.2 Workflow
1.  **Measure**: `Carbon Footprint Analyst` が活動量データ（電力、燃料）を収集。
2.  **Optimize**: `Green AI Optimizer` が、推論モデルの軽量化（蒸留）を提案。
3.  **Disclose**: `ESG Disclosure Expert` が、ISSB基準に沿った開示資料を作成。

## 3. Bundled Resources
*   `ESG_MANUAL.md`: ESGデータ収集マニュアル

## 4. Safety
*   **Greenwashing**: 実態を伴わない見せかけの環境配慮（グリーンウォッシュ）を厳しく排除する。