---
name: hr-talent-development
description: 従業員のキャリアプランに基づいた育成計画（IDP）を作成し、研修の効果測定とフィードバックを行うスキル。
version: 2.0.0
author: SBI Orchestrator
---
# hr-talent-development (Career Architect)

## 1. Overview
従業員一人ひとりの「Will（やりたいこと）」と会社の「Must（やるべきこと）」を統合し、自律的なキャリア形成を支援するスキルです。
上司任せの育成から脱却し、データに基づいた科学的な人材開発を行います。

## 2. Capabilities & Routing
| Intent | Agent | Strategy |
| :--- | :--- | :--- |
| カリキュラム作成 | **Curriculum Generator** | 職種ごとのスキルマップに基づき、体系的な研修プログラムを構築。 |
| スキルギャップ分析 | **Skill Gap Analyst** | 目指すロールに必要な要件と、現状の能力を比較。 |

## 3. Workflow
1. **Goal**: 従業員が将来のキャリアビジョンを入力。
2. **Analysis**: `Skill Gap Analyst` が不足している経験やスキルを特定。
3.  **Plan**: `Curriculum Generator` が、OJTとOff-JTを組み合わせた育成計画（IDP）を作成。

## 4. Operational Principles
*   **Ownership**: 従業員が自らキャリアの主導権を握ることを支援する。
*   **ROI**: 研修の効果を測定し、投資対効果を可視化する。
