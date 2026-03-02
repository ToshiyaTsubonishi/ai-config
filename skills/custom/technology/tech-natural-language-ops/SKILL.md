---
name: tech-natural-language-ops
description: ユーザーの自然言語入力を、システムが実行可能なコマンドやSQLに安全に変換する「言葉のコンパイラ」スキル。
version: 1.0.0
author: Gemini Skill Creator
---
# tech-natural-language-ops (Prompt Engineering)

## 1. Overview
**What is this?**
「最近調子のいい株を教えて」といった曖昧なユーザーの発話を、`SELECT * FROM stocks WHERE ...` のような厳密なクエリに変換するスキルです。
意図解釈（Intent Recognition）と、実行コマンドのサニタイズ（無害化）を行い、対話型インターフェースを実現します。

**When to use this?**
*   チャットボット経由でDB検索やAPI操作を行わせたい場合。
*   ユーザーの属性（初心者/プロ）に合わせて、回答のトーンや専門用語のレベルを調整する場合。
*   生成されたSQLやシェルコマンドに、危険な操作が含まれていないかチェックする場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| コマンド検査・無害化 | **Command Sanitizer** | `../../agents/command-sanitizer.md` |
| 意図解釈・スロット抽出 | **Intent Compiler** | `../../agents/intent-compiler.md` |
| ペルソナ調整・翻訳 | **Persona Adapter** | `../../agents/persona-adapter.md` |

### 2.2 Workflow
1.  **Parse**: `Intent Compiler` が発話を解析し、「銘柄検索」という意図と「ITセクター」というパラメータを抽出。
2.  **Generate**: 実行コード（SQL等）を生成。
3.  **Sanitize**: `Command Sanitizer` が `DROP TABLE` などの危険な記述がないか検査。
4.  **Adapt**: `Persona Adapter` が、初心者には優しく、プロには簡潔に結果を表示。

## 3. Bundled Resources
*   No specific assets listed.

## 4. Safety
*   **Injection**: SQLインジェクションやOSコマンドインジェクションを完全に防ぐ。