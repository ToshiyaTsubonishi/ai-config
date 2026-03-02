---
name: tech-governance-as-code
description: ポリシー（ルール）をコードとして記述し、システムの挙動を自動的に統制する「Governance as Code」を実現するスキル。
version: 1.0.0
author: Gemini Skill Creator
---
# tech-governance-as-code (Automated Compliance)

## 1. Overview
**What is this?**
「利益相反取引の禁止」や「アクセス権限の制限」といった人間のルールを、プログラム（Rego等）に変換し、システムレベルで強制するスキルです。
事後チェックではなく、APIコールやデプロイの瞬間にブロックすることで、事故を未然に防ぎます。

**When to use this?**
*   Kubernetesのデプロイ時に、セキュリティ設定（Pod Security Policy）を強制する場合。
*   エージェントが許可されていないAPIを叩こうとした時に、それを遮断する場合。
*   Terraformのコードが、コンプライアンス基準を満たしているか静的解析する場合。

## 2. Capability Instructions

### 2.1 Routing
| User Intent | Target Agent | File Path |
| :--- | :--- | :--- |
| アクション遮断・介入 | **Action Interceptor** | `../../agents/action-interceptor.md` |
| ポリシー記述・コード化 | **Policy Coder Rego** | `../../agents/policy-coder-rego.md` |

### 2.2 Workflow
1.  **Define**: 法務部門が定めたルールを、`Policy Coder Rego` がOpen Policy Agent (OPA) 用のコードに変換。
2.  **Intercept**: `Action Interceptor` が全てのエージェント操作をフック。
3.  **Evaluate**: ポリシーコードと照合し、Allow/Denyを判定。

## 3. Bundled Resources
*   No specific assets listed.

## 4. Safety
*   **Availability**: ポリシーエンジンがダウンしても、システム全体が停止しないようフェイルオープン/クローズを適切に設定する。