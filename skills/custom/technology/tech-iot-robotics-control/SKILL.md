---
name: tech-iot-robotics-control
description: ロボット（ドローン、UGV）やIoTデバイス群（Fleet）を制御し、物理世界でのタスクを実行させるロボティクス・スキル。
version: 1.0.0
author: Gemini Skill Creator
---
# tech-iot-robotics-control (Physical Operations)

## 1. Overview
**What is this?**
サイバー空間のAIと、物理空間のロボットを接続するスキルです。
ROS 2（Robot Operating System）を介して、複数のロボットに協調動作（Swarm）をさせたり、エッジ側でのリアルタイム推論を行います。

**When to use this?**
*   ドローンを使った設備点検や配送を行う場合。
*   オフィスの清掃ロボットや警備ロボットを集中管理する場合。
*   工場のAGV（無人搬送車）のルートを最適化する場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| エッジAI・リアルタイム制御 | **Edge Sensing Agent** | `../../agents/edge-sensing-agent.md` |
| フリート管理・群制御 | **Physical Fleet Orchestrator** | `../../agents/physical-fleet-orchestrator.md` |

### 2.2 Workflow
1.  **Plan**: `Physical Fleet Orchestrator` が全体のタスクを分割し、各ロボットに割り当て。
2.  **Act**: 各ロボットが移動開始。
3.  **Avoid**: 障害物に遭遇した場合、`Edge Sensing Agent` が瞬時に回避行動をとる。

## 3. Bundled Resources
*   No specific assets listed.

## 4. Safety
*   **Safety First**: 人間への物理的危害（衝突など）を絶対に防ぐ安全機構（Safety Layer）を組み込む。