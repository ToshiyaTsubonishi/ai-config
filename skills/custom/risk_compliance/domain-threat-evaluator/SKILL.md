---
name: domain-threat-evaluator
description: 類似ドメイン（タイポスクワッティング）を検知し、フィッシング詐欺やブランド毀損のリスクを評価するセキュリティスキル。
version: 2.0.0
author: SBI Orchestrator
---
# domain-threat-evaluator (Domain Sentry)

## 1. Overview
SBIグループのデジタルブランドを守り、顧客を偽サイト（フィッシング）から保護するための防衛スキルです。
正規ドメインから一文字違いのドメイン（Typosquatting）を世界中から探し出し、悪用される前に無害化します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| ドメイン・類似文字スキャン | **Domain Scanner** | dnstwist等のアルゴリズムを用い、数千通りのドメイン候補を自動チェック。 |
| リスク評価・Takedown支援 | **Risk Analyzer** | IP、DNS、Webコンテンツから危険度を判定し、法的措置の優先順位を決定。 |

## 3. Workflow
1. **Detect**: `trademark-brand-monitor` 連携により、新しく取得された不審なドメインを捕捉。
2. **Scan**: `Domain Scanner` がサーバーの稼働状況や、偽のログイン画面が存在しないか確認。
3. **Alert**: リスクが高い場合、`sbi-public-relations` と連携し、顧客への注意喚起とプロバイダーへの削除要請（Takedown）を実施。

## 4. Operational Principles
* **Proactive Defense**: 被害が出る前にドメインを特定し、先手を打つ。
* **Evidence Gathering**: 裁判や警察への通報に使える証拠を、デジタルフォレンジック形式で保存。
