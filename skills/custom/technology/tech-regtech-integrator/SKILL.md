---
name: tech-regtech-integrator
description: 金融規制（Regulation）への対応をテクノロジーで効率化し、報告業務の自動化やコンプライアンスコストの削減を実現するスキル。
version: 1.0.0
author: Gemini Skill Creator
---
# tech-regtech-integrator (RegTech Ops)

## 1. Overview
**What is this?**
金融機関の「守り」を鉄壁にするスキルです。
金融庁や日銀への報告データ作成を自動化し、また法令改正情報をリアルタイムでキャッチアップすることで、コンプライアンス違反のリスクを極小化します。

**When to use this?**
*   疑わしい取引（STR）を検知し、当局への届出書をドラフトする場合。
*   自己資本比率規制などの複雑な計算ロジックをシステムに実装する場合。
*   新しい法規制がビジネスに与える影響を分析する場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| 定期報告・STR作成 | **Auto Reporting Bot** | `../../agents/auto-reporting-bot.md` |
| 規制当局API連携 | **Regulatory API Bridge** | `../../agents/regulatory-api-bridge.md` |

### 2.2 Workflow
1.  **Monitor**: 取引データを常時監視。
2.  **Detect**: 閾値を超える送金や、制裁対象国との取引を検知。
3.  **Report**: `Auto Reporting Bot` が届出書を作成し、`Regulatory API Bridge` が当局システムに送信。

## 3. Bundled Resources
*   No specific assets listed.

## 4. Safety
*   **Audit Trail**: 報告データの改竄を防ぐため、作成・承認・送信の全プロセスをログに残す。
