---
name: ga-facility-management
description: オフィスの空調、照明、清掃、および座席予約をIoTとAIで最適化し、快適で効率的な執務環境を提供するスキル。
version: 2.0.0
author: SBI Orchestrator
---
# ga-facility-management (Smart Workplace)

## 1. Overview
オフィスを単なる「場所」から「生産性を高めるデバイス」へと進化させるスキルです。
IoTセンサーとAIを駆使し、エネルギー効率と従業員の快適性（Wellness）を同時に追求します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| ビル設備制御・省エネ | **Smart Building Operator** | 人流や気候に合わせて、空調・照明をリアルタイム制御。 |
| オフィス戦略・レイアウト | **Spatial Strategy Agent** | 稼働データを分析し、ABW（Activity Based Working）に最適な配置を提案。 |

## 3. Workflow
1. **Sense**: 温度、湿度、CO2、騒音、人流データを収集。
2. **Optimize**: `Smart Building Operator` が、快適性を保ちつつ電力を最小化する設定を適用。
3. **Plan**: `Spatial Strategy Agent` が、「集中エリアが不足している」等の課題を発見し、模様替えを提案。

## 4. Operational Principles
*   **Sustainability**: 省エネ法やSBTi目標に貢献する運用を行う。
*   **Comfort**: 従業員の健康と集中力を最優先する（CO2濃度管理など）。
