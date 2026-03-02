---
name: tech-legacy-migration-engine
description: COBOL/JCL等のレガシーコードを解析し、Rust/Go等のモダン言語へ安全に変換（Transpile）するマイグレーション専門スキル。
version: 1.0.0
author: Gemini Skill Creator
---
# tech-legacy-migration-engine (Code Archaeologist)

## 1. Overview
**What is this?**
仕様書が失われた古いシステム（ブラックボックス）の中身をコードから解読し、ビジネスロジックを抽出して、現代の技術で再実装するスキルです。
「動いているから触るな」という呪縛を解き、システムを再び進化可能な状態にします。

**When to use this?**
*   スパゲッティ化したCOBOLコードから、仕様書を逆生成（リバースエンジニアリング）する場合。
*   Javaの古いバージョンを、最新のRustやGoに書き換える場合。
*   移行前後の挙動が一致しているか、自動テストで検証する場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| レガシーコード解析 | **COBOL Archaeologist** | `../../agents/cobol-archaeologist.md` |
| 挙動一致検証・テスト | **Legacy Verifier** | `../../agents/legacy-verifier.md` |
| コード変換・実装 | **Rust Transpiler** | `../../agents/rust-transpiler.md` |

### 2.2 Workflow
1.  **Dig**: `COBOL Archaeologist` がコードの依存関係とデータフローを可視化。
2.  **Transpile**: `Rust Transpiler` がメモリ安全なRustコードに変換。
3.  **Test**: `Legacy Verifier` が新旧システムに同じ入力を与え、出力が完全に一致することを確認（Golden Master Testing）。

## 3. Bundled Resources
*   No specific assets listed.

## 4. Safety
*   **Regression**: 既存機能の退行（デグレ）を絶対に防ぐため、テストカバレッジ100%を目指す。