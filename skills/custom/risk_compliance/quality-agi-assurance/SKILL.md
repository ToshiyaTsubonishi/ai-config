---
name: quality-agi-assurance
description: AIシステム（AGI）の品質を保証するためのテスト自動化、回帰テスト、および振る舞いテストを行うQAスキル。
version: 2.0.0
author: SBI Orchestrator
---
# quality-agi-assurance (AI QA)

## 1. Overview
確率的に動作するAIシステムの品質を、「運」任せにせず工学的に保証するスキルです。
数千パターンのテストケースを自動生成・実行し、プロンプト変更やモデル更新によるデグレ（品質低下）を水際で防ぎます。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 振る舞いテスト・シナリオ生成 | **Behavioral Test Engineer** | 意地悪なユーザーや想定外の入力に対するAIの挙動をテスト。 |
| 回帰テスト・自動実行 | **Regression QA Bot** | 過去の成功パターンが現在も機能するかを一括チェック。 |

## 3. Workflow
1. **Design**: `Behavioral Test Engineer` が、エージェントの性格（Persona）に合わせたテストシナリオを作成。
2.  **Execute**: `Regression QA Bot` がCI/CDパイプライン上でテストを実行。
3.  **Evaluate**: 回答の正確性、安全性、トーンの一貫性をスコアリング。
4.  **Report**: 品質基準を満たさない場合、リリースをブロック。

## 4. Operational Principles
*   **Safety**: テスト環境と本番環境を分離し、テストデータが流出しないようにする。
*   **Coverage**: 正常系だけでなく、異常系（Edge Case）のテストを重視する。
