---
name: regional-super-app-core
description: 金融、移動、行政、消費を統合し、住民の生活を一気通貫で支える「地域生活OS」の核心スキル。
version: 2.0.0
author: SBI Orchestrator
---
# regional-super-app-core (Life OS)

## 1. Overview
地域金融機関（例：島根銀行）のアプリを、単なるバンキングアプリから、地域住民の生活全般（Life OS）を支えるスーパーアプリへと進化させるスキルです。
MaaS（移動）、行政手続き、医療、クーポンの機能を統合し、住民IDと決済基盤で結びつけます。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 外部サービス連携・ミニアプリ統合 | **Lifestyle Service Integrator** | タクシー、病院、行政システムとAPI連携し、アプリ内で完結させる。 |
| 地域トークン・ポイント管理 | **Regional Token Manager** | 地域内でのみ流通するポイントや通貨を発行し、経済圏を作る。 |

## 3. Workflow
1. **Integrate**: `Lifestyle Service Integrator` が地元のタクシー会社や病院のシステムとAPI連携。
2.  **Incentivize**: `Regional Token Manager` が、歩数やボランティア活動に応じてトークンを付与（Health-to-Earn）。
3.  **Circulate**: トークンを地元商店街での決済に利用させ、地域経済を回す。

## 4. Operational Principles
*   **Security**: 決済機能と個人情報（ID）を扱うため、金融グレードのセキュリティを担保する。
*   **Usability**: 高齢者でも使えるシンプルなUI（`tech-frontend-engineering-accessible`）を徹底する。
