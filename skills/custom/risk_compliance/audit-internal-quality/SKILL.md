---
name: audit-internal-quality
description: 業務プロセスが社内規定やISO規格に適合しているかを監査し、品質向上を支援するスキル。
version: 2.0.0
author: SBI Orchestrator
---
# audit-internal-quality (Internal Audit)

## 1. Overview
「正しい倫理的価値観」に基づく業務遂行を保証するための監査スキルです。
不備を見つける「摘発」ではなく、より効率的で安全なプロセスへと導く「改善」を主眼に置きます。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| プロセス逸脱検知 | **Process Compliance Miner** | システムログから、規定外の操作（ショートカット等）を自動抽出。 |
| 取引データのリアルタイム監査 | **Real-Time Tx Auditor** | 送金や購買の瞬間、不正やミスがないかAIが瞬時に判定。 |

## 3. Workflow
1. **Analyze**: `Process Compliance Miner` が現場の「実態」を可視化。
2. **Review**: 監査マニュアルおよびJ-SOX基準に照らし、リスクを評価。
3. **Counsel**: 現場の負担を減らしつつ安全性を高めるための、具体的な手順変更を提案。

## 4. Operational Principles
* **Objectivity**: 忖度のない客観的なデータに基づく評価。
* **Agility**: 事件が起きた後ではなく、起きる前に防ぐ（Continuous Monitoring）。
