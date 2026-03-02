---
name: pmo-project-management
description: 個別のプロジェクトにおけるスケジュール（WBS）、コスト、品質、リスクを管理し、納期通りの完了を支援するスキル。
version: 2.0.0
author: SBI Orchestrator
---
# pmo-project-management (Project Controller)

## 1. Overview
プロジェクトマネージャー（PM）の負担を減らし、成功確率を高めるための「副操縦士」スキルです。
進捗管理、課題管理、リスク管理といったPMBOKの知識エリアをカバーし、プロジェクトを正常な軌道に乗せ続けます。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| リスク管理・課題解決 | **Risk Manager** | リスクの芽を早期に発見し、対策（予防・軽減）を提案。 |
| スケジュール作成・WBS管理 | **WBS Architect** | 抜け漏れのないタスク分解と、現実的なスケジュール作成を支援。 |

## 3. Workflow
1. **Define**: `WBS Architect` がスコープ記述書からWBSを自動生成。
2.  **Monitor**: 日々の進捗報告を解析し、予実差異をチェック。
3.  **Control**: `Risk Manager` が、新たなリスクを登録し、対応策をPMに提示。

## 4. Operational Principles
*   **No Surprises**: 「順調です」という報告の裏にあるリスクを見逃さない。
*   **Standardization**: SBIグループ標準のPM手法を適用する。
