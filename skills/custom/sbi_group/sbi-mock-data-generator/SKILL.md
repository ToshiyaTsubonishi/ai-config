---
name: sbi-mock-data-generator
description: システムテストやデモのために、本物そっくりの個人情報、取引履歴、および行動ログ（シンセティックデータ）を生成するスキル。
version: 2.0.0
author: SBI Orchestrator
---
# sbi-mock-data-generator (Synthetic Factory)

## 1. Overview
機密性の高い「本番データ」を使わずに、AIモデルの学習やシステム開発を行うためのスキルです。
統計的な特性（分布や相関）を維持しつつ、数学的に合成された「実在しないデータ（シンセティックデータ）」を生成し、プライバシーと開発スピードの両立を実現します。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| 属性・ペルソナ生成 | **Persona Data Builder** | 日本の人口統計に基づき、リアルな氏名・住所・世帯構成を生成。 |
| 金融取引ログ生成 | **Synthetic Transaction Crafter** | 給与、支払い、投資行動など、時間軸に沿った論理的なログを作成。 |

## 3. Workflow
1. **Define**: 必要なデータのスキーマ（カラム名、データ型）を定義。
2. **Profile**: `Persona Data Builder` が、年齢や年収の分布を指定通りに生成。
3. **Trace**: `Synthetic Transaction Crafter` が、「入金がないのに出金される」といった論理矛盾のない履歴を構築。
4. **Export**: CSVやJSON、SQL形式で出力。

## 4. Operational Principles
* **Zero PII**: 実在の個人情報が1件も含まれないことを数学的に保証する。
* **Consistency**: 名簿データと取引データの整合性（例：未成年がローンを組まない）を保つ。
