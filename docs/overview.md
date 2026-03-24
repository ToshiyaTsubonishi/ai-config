# ai-config 概要ガイド

## ai-config とは

`ai-config` は、AI agent が必要な Skill / MCP を **必要なときだけ動的に見つけるための selector platform** です。

ひとことで言うと:

> AI agent のための capability broker

## 何を解決するか

AI agent に大量の skill や MCP 情報を事前投入すると:

- コンテキストを圧迫する
- 不要な候補が増える
- selection quality が下がる
- provenance や ownership が曖昧になる

`ai-config` は catalog / index / selector を通して、必要な候補だけを返します。

## いまの設計の重心

### 1. Selector Platform

- Skill / MCP catalog
- ToolRecord normalization
- hybrid retrieval / RAG
- selector MCP
- selector-serving

### 2. Planner Artifact

- candidate retrieval
- approved plan generation
- plan validation
- controlled replan

### 3. Boundary, not runtime

approved plan の execution runtime は重要ですが、`ai-config` の主役ではありません。
実行は stable boundary 越しに dispatch runtime へ渡します。

## 全体像

```text
Agent
  -> ai-config-selector
  -> candidate list
  -> ai-config-agent plan
  -> ApprovedPlan
  -> ai-config-agent execute-approved-plan
  -> ApprovedPlanExecutionRequest
  -> dispatch runtime
```

## 用語

| 用語 | 意味 |
|---|---|
| selector | Skill / MCP 候補を返す lookup 層 |
| planner | approved plan artifact を作る層 |
| execution boundary | plan を runtime に渡す stable contract |
| dispatch runtime | approved plan を実行する外側の runtime |
| selector-serving | selector read API を HTTP で公開する標準 surface |

## 標準運用

```bash
ai-config-agent search "eslint config"
ai-config-agent plan "codex で修正"
ai-config-agent execute-approved-plan --plan ./approved-plan.json
```

selector-serving を使う deploy では:

```bash
PORT=8080 ai-config-selector-serving --repo-root . --index-dir ./.index
```

## この repo の価値

`ai-config` の価値は、外部 runtime を自前で抱えることではなく:

- 正しい候補を見せること
- plan artifact を安定して作ること
- provenance と ownership を維持すること
- read-only runtime で安全に serving できること

にあります。
