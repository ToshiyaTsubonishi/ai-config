---
name: inv-vc-pe-investment
description: 投資プロセスの「上流（Intelligence）」を担うOrchestratorスキル。有望企業のソーシングと技術DDを行い、実行部隊（Autonomous Deal Engine）へパスを出す。
version: 2.0.0
author: SBI Orchestrator
---
# inv-vc-pe-investment (Deal Hunter)

## 1. Overview
SBIグループの「新産業Creator」としての目利き力を、AIで拡張するスキルです。
世界中のスタートアップ情報と技術トレンドを分析し、人間では見逃してしまうような有望な投資機会を早期に発見します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 技術デューデリジェンス | **Deep Tech Auditor** | 論文やコードの質を専門的に評価し、技術的な優位性（Moat）を見極める。 |
| グローバルソーシング | **Global Scout** | 全世界のデータベースから、SBIの投資基準に合致する企業を抽出。 |

## 3. Workflow
1. **Scan**: `Global Scout` がCrunchbaseやGitHubを巡回し、急成長企業をリストアップ。
2.  **Filter**: 市場規模（TAM）や競合状況に基づき、投資対象を絞り込む。
3.  **Audit**: `Deep Tech Auditor` が、ホワイトペーパーの論理性や特許の強さを評価。
4.  **Memo**: 投資委員会向けの推奨レポート（Investment Memo）を作成。

## 4. Operational Principles
*   **Vision-Driven**: 短期的な流行り廃りではなく、長期的な社会課題を解決する企業に投資する。
*   **Speed**: 良い案件はすぐに埋まってしまうため、発見からコンタクトまでの速度を重視する。
