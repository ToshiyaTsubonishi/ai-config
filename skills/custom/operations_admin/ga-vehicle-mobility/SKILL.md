---
name: ga-vehicle-mobility
description: 社用車や役員車の配車、メンテナンス、およびEV化を推進し、移動コストと環境負荷を削減するスキル。
version: 2.0.0
author: SBI Orchestrator
---
# ga-vehicle-mobility (Fleet Ops)

## 1. Overview
「移動」をサービスとして最適化（MaaS）するスキルです。
役員車の運行管理だけでなく、営業車のEV化やカーシェアリングの導入を通じて、コストとCO2排出量を同時に削減します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 配車・ルート最適化 | **Fleet Dispatcher** | リアルタイムの交通状況を考慮し、最短・最安のルートを案内。 |
| 車両整備・EV管理 | **Maintenance Bot** | 車検、保険、充電状況を一元管理し、ダウンタイムを防ぐ。 |

## 3. Workflow
1. **Reserve**: 社員がアプリから車両を予約。
2.  **Dispatch**: `Fleet Dispatcher` が、空き車両またはタクシーを割り当て。
3.  **Drive**: 走行データを記録し、安全運転診断を実施。
4.  **Care**: `Maintenance Bot` が、走行距離に応じて点検を予約。

## 4. Operational Principles
*   **Safety**: 事故ゼロを目指し、テレマティクスを活用した指導を行う。
*   **Green**: 2030年までに社用車の100%EV化を目指す。
