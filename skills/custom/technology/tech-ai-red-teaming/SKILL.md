---
name: tech-ai-red-teaming
description: 生成AIやエージェントシステムに対する敵対的攻撃（Red Teaming）を行い、脆弱性と倫理的リスクを洗い出すセキュリティスキル。
version: 1.0.0
author: Gemini Skill Creator
---
# tech-ai-red-teaming (AI Stress Test)

## 1. Overview
**What is this?**
リリース前のAIモデルやエージェントに対し、攻撃者（ハッカー）の視点で様々な攻撃を仕掛けるスキルです。
プロンプトインジェクション、ジェイルブレイク、または偏見のある回答を引き出すテストを行い、システムの堅牢性を高めます。

**When to use this?**
*   LLMを組み込んだアプリのリリース前に、安全性テストを行う場合。
*   RAG（検索拡張生成）システムが、悪意あるドキュメントを読み込んでしまわないか検証する場合。
*   AIの倫理ガイドラインが機能しているか、ストレステストを行う場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| プロンプトインジェクション攻撃 | **Injection Fuzzer** | `../../agents/injection-fuzzer.md` |
| ジェイルブレイク・倫理突破テスト | **Jailbreak Tester** | `../../agents/jailbreak-tester.md` |

### 2.2 Workflow
1.  **Attack**: `Jailbreak Tester` が「DAN」等の手法を用いて、AIのガードレール突破を試みる。
2.  **Inject**: `Injection Fuzzer` が、隠しコマンドを含むテキストを読み込ませる。
3.  **Report**: 成功してしまった攻撃（脆弱性）をレポートにまとめ、対策を提示。

## 3. Bundled Resources
*   No specific assets listed.

## 4. Safety
*   **Controlled Environment**: 攻撃テストは必ずサンドボックス環境で行い、本番システムには影響を与えない。