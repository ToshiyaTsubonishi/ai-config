---
name: sbi-risk-intelligence
description: ダークウェブやSNSを含むオープンソース・インテリジェンス（OSINT）を駆使し、SBIグループに対する脅威を予知する諜報スキル。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-risk-intelligence (Cyber Intel)

## 1. Overview
攻撃される前に「予兆」を掴み、先手で防御するためのインテリジェンス・スキルです。
ダークウェブの深淵から、SNS上の不自然なナラティブの拡散まで、デジタルの全領域を監視し、グループの資産とレピュテーションを守ります。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| ダークウェブ監視・漏洩検知 | **Darkweb Monitor** | 漏洩したID、パスワード、ソースコードの売買を常時監視。 |
| SNS分析・組織的攻撃検知 | **OSINT Analyst** | 特定団体による不買運動やサイバー攻撃予告を早期に捕捉。 |

## 3. Workflow
1. **Sweep**: `Darkweb Monitor` がハッカーフォーラムをクローリング。
2. **Scan**: 漏洩したデータに、SBIに関連するドメインやメールアドレスが含まれていないか確認。
3. **Trace**: `OSINT Analyst` が、XやRedditでの不自然な投稿（Botによる拡散）を分析。
4. **Alert**: 脅威レベルを判定し、CSIRTや広報部に警告を発報。

## 4. Operational Principles
* **Early Warning**: 100%の確証がなくても、蓋然性が高い段階でアラートを出す。
* **Legality**: 自らがハッキングを行うことはせず、公開情報の収集（OSINT）に徹する。
