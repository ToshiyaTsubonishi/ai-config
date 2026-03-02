---
name: sbi-security-warden
description: 物理的なオフィスセキュリティと、監視カメラ映像のAI解析を組み合わせた、次世代の警備システム運用スキル。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-security-warden (Safe Campus)

## 1. Overview
「物理空間」の安全をAIで監視・制御するスキルです。
オフィスの入退室ゲート、監視カメラ、スマートロックを統合し、不審者の侵入検知や、深夜残業者の安否確認、VIP来訪時の警備強化を自動化します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 入退室・スマートロック制御 | **Perimeter Access Guard** | 従業員のID、顔認証、スマホの位置情報を組み合わせてゲートを自動開閉。 |
| 映像解析・不審挙動検知 | **Vision Surveillance AI** | カメラ映像から、置き去り荷物、転倒者、徘徊者などをリアルタイム検知。 |

## 3. Workflow
1. **Monitor**: `Vision Surveillance AI` がオフィス全域のライブ映像を解析。
2. **Detect**: 「登録されていない人物が、深夜にサーバー室付近を徘徊」という異常事態を検知。
3. **Action**: `Perimeter Access Guard` がサーバー室の電子錠をロックし、警備員に通報。
4. **Alert**: 付近にいる従業員に、安全な場所への移動を指示。

## 4. Operational Principles
* **Privacy by Design**: プライバシーに配慮し、不要な顔データの保存は行わず、匿名化された特徴量のみを扱う。
* **Zero Blind Spots**: センサーとカメラを連携させ、死角のない警備体制を構築する。
