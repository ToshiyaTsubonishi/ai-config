---
name: tech-datarobot-integration
description: DataRobotのAutoML機能と連携し、ビジネス課題（予測、分類）を解決するAIモデルを自動生成・運用するスキル。
version: 1.0.0
author: Gemini Skill Creator
---
# tech-datarobot-integration (AutoML Master)

## 1. Overview
**What is this?**
SBIグループが導入している「DataRobot」をエージェントから操作し、データサイエンティストでなくとも高度な予測モデルを作成できるスキルです。
データのアップロード、モデル学習、デプロイ、そして精度の監視（MLOps）を自動化します。

**When to use this?**
*   「来月の解約率を予測したい」といったビジネス課題に対し、素早くモデルを作りたい場合。
*   大量の特徴量の中から、予測に効く重要な変数を特定したい場合。
*   本番環境で稼働中のモデルの精度劣化（ドリフト）を検知する場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| モデル稼働監視・ドリフト検知 | **AI Ops Monitor** | `../../agents/ai-ops-monitor.md` |
| モデル作成・学習自動化 | **Model Factory Agent** | `../../agents/model-factory-agent.md` |

### 2.2 Workflow
1.  **Upload**: CSVデータをDataRobotに投入。
2.  **Train**: `Model Factory Agent` が最適なアルゴリズム（XGBoost, LightGBM等）を自動選定し、学習。
3.  **Deploy**: 精度が最も高いモデルをAPIとして公開。
4.  **Monitor**: `AI Ops Monitor` が予測精度を常時監視し、劣化したら再学習を指示。

## 3. Bundled Resources
*   No specific assets listed.

## 4. Safety
*   **Explainability**: AIの判断根拠（SHAP値など）を必ず提示し、ブラックボックス化を防ぐ。