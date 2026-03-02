---
name: tech-rust-mission-critical
description: 高い信頼性とパフォーマンスが要求される金融コアシステムを、Rust言語を用いて開発・最適化するエンジニアリングスキル。
version: 1.0.0
author: Gemini Skill Creator
---
# tech-rust-mission-critical (Rust Core)

## 1. Overview
**What is this?**
「絶対に止まらない、間違えない」ことが求められる金融システムの核（Core）を構築するスキルです。
Rustの所有権モデルを活かしてメモリ安全性を担保しつつ、ゼロコスト抽象化によりC++並みのパフォーマンスを実現します。

**When to use this?**
*   勘定系システム（Ledger）やマッチングエンジンの開発。
*   既存のC/C++コードをRustに書き換え（Rewrite in Rust）、安全性を高める場合。
*   レイテンシ（遅延）にシビアなHFTシステムのチューニングを行う場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| パフォーマンス最適化 | **Rust Perf Optimizer** | `../../agents/rust-perf-optimizer.md` |
| 安全性監査・Borrow Checker対策 | **Rust Safety Auditor** | `../../agents/rust-safety-auditor.md` |

### 2.2 Workflow
1.  **Code**: `Rust Transpiler`（`tech-legacy-migration-engine`参照）等で生成されたコードをレビュー。
2.  **Audit**: `Rust Safety Auditor` が `unsafe` ブロックやメモリリークの可能性を静的解析。
3.  **Tune**: `Rust Perf Optimizer` がプロファイリングを行い、ボトルネックを解消。

## 3. Bundled Resources
*   No specific assets listed.

## 4. Safety
*   **Panic Free**: 本番環境で `panic!`（強制終了）が発生しないよう、エラーハンドリング（Result型）を徹底する。
