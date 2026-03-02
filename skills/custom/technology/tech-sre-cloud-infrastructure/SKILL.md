---
name: tech-sre-cloud-infrastructure
description: Google Cloud, AWS, Azureを組み合わせたマルチクラウド環境において、信頼性（SRE）とコスト効率を最大化するインフラ構築スキル。
version: 1.0.0
author: Gemini Skill Creator
---
# tech-sre-cloud-infrastructure (Cloud Native)

## 1. Overview
**What is this?**
SBIグループの巨大なインフラを「コード」として管理（IaC）し、運用の自動化と安定稼働を実現するスキルです。
マルチクラウド構成により、特定のクラウドベンダーの障害に左右されない強靭なシステムを作ります。

**When to use this?**
*   Terraformでインフラを構築・変更する場合。
*   SLO（サービスレベル目標）に基づいたエラーバジェット管理を行う場合。
*   クラウドコスト（FinOps）を分析し、リザーブドインスタンスやスポットインスタンスの活用を提案する場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| クラウドコスト最適化 | **Cloud FinOps Optimizer** | `../../agents/cloud-finops-optimizer.md` |
| インフラ構築・管理 (IaC) | **IaC Architect** | `../../agents/iac-architect.md` |
| SRE・信頼性エンジニアリング | **SRE Sentinel** | `../../agents/sre-sentinel.md` |

### 2.2 Workflow
1.  **Define**: `IaC Architect` がインフラ構成をHCL（HashiCorp Configuration Language）で記述。
2.  **Monitor**: `SRE Sentinel` がレイテンシやエラー率を監視。
3.  **Optimize**: `Cloud FinOps Optimizer` が、無駄なリソースを削除・縮小。

## 3. Bundled Resources
*   `SRE_MANUAL.md`: SRE運用標準マニュアル

## 4. Safety
*   **Approval**: インフラへの変更（Apply）は、必ずプルリクエストの承認を経てから自動実行する。
