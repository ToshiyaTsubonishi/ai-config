---
name: tech-quantum-finance
description: 量子コンピューティング技術を金融実務（ポートフォリオ最適化、オプション価格算定）に応用する先端技術スキル。
version: 1.0.0
author: Gemini Skill Creator
---
# tech-quantum-finance (Quantum Leap)

## 1. Overview
**What is this?**
従来の古典コンピュータでは計算困難な金融問題を、量子アニーリングやゲート方式量子コンピュータを用いて解決するスキルです。
ポートフォリオの組み合わせ最適化や、モンテカルロ・シミュレーションの高速化を実現します。

**When to use this?**
*   数千銘柄のポートフォリオ最適化問題を、ミリ秒単位で解きたい場合。
*   複雑なデリバティブ商品の価格を、量子アルゴリズムで精緻に計算する場合。
*   量子と古典のハイブリッド環境（HPC）を構築する場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| 量子/古典ハイブリッド制御 | **Hybrid Runtime Orchestrator** | `../../agents/hybrid-runtime-orchestrator.md` |
| 量子アルゴリズム設計 | **Quantum Algo Architect** | `../../agents/quantum-algo-architect.md` |

### 2.2 Workflow
1.  **Formulate**: 金融問題をイジングモデルや量子回路（QUBO）に変換。
2.  **Execute**: `Hybrid Runtime Orchestrator` が、問題の規模に応じて量子（QPU）か古典（GPU）かを振り分け。
3.  **Optimize**: `Quantum Algo Architect` がQAOAやVQEなどのアルゴリズムを適用。

## 3. Bundled Resources
*   No specific assets listed.

## 4. Safety
*   **Error Correction**: 現在の量子コンピュータ（NISQ）はエラーが多いため、必ず古典計算で検証を行う。