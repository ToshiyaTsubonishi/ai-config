# ai-config

AI agent 向けの **動的 Skill / MCP 選択基盤**。`ai-config` は selector platform と planner artifact generation に集中し、execution runtime は stable boundary の向こうへ逃がします。

## Core Responsibility

`ai-config` が正本として持つもの:

- Skill / MCP source の catalog と ownership
- vendor / import / provenance 管理
- `ToolRecord` 正規化と registry
- build-time index と runtime validation
- hybrid retrieval / RAG
- selector API / MCP server
- `ai-config-selector-serving` という標準 HTTP deploy surface
- planner library と approved plan artifact
- downstream MCP catalog / lookup / bridge

`ai-config` が直接抱え込まないもの:

- approved plan の実行 runtime
- plan execution の DAG / parallelism / retry / context handoff の詳細実装
- dispatch repo の内部構造

## Responsibility Split

| Layer | Role | In This Repo |
|---|---|---|
| `selector` | Skill / MCP lookup, ranking, detail lookup, downstream MCP discovery | yes |
| `planner` | candidate retrieval, plan artifact generation, plan validation, controlled replan | yes |
| `execution` | approved plan boundary, subprocess / package contract, tool executor abstraction | yes |
| `dispatch runtime` | approved plan execution, dependency DAG, parallelism, retry, context handoff | boundary only |

標準フロー:

1. Agent が `ai-config-selector` を呼んで候補を得る
2. 必要なときだけ `ai-config-agent plan ...` で approved plan を作る
3. 実行は `ai-config-agent execute-approved-plan ...` が stable boundary 経由で dispatch runtime に委譲する

## Standard Surfaces

### Selector MCP

`ai-config-selector` は `ai-config-mcp-server` で公開される selector MCP です。

- `search_tools`
- `get_tool_detail`
- `list_categories`
- `get_tool_count`
- `list_mcp_server_tools`
- `call_mcp_server_tool`

### Selector Serving

`ai-config-selector-serving` は Cloud Run / HTTP 用の **標準 deploy surface** です。

- endpoint: `/mcp`
- health: `/healthz`
- readiness: `/readyz`
- runtime mode: read-only
- startup で `.index` contract を fail-fast validation

### Planner CLI

`ai-config-agent` は search / plan / execute を明示的に分けた planner-facing CLI です。

```bash
# search only
ai-config-agent search "eslint config" --index-dir ./.index

# plan only
ai-config-agent plan "codex でバグを修正" --index-dir ./.index

# approved plan execution via stable boundary
ai-config-agent execute-approved-plan --plan ./approved-plan.json --index-dir ./.index

# stable contract schema
ai-config-agent schema approved-plan
ai-config-agent schema approved-plan-execution-request
ai-config-agent schema approved-plan-execution-result
```

互換のため、従来の `--search-only` / `--plan-only` / `--execute-plan` も当面は維持します。

### Dispatch Runtime Boundary

`ai-config` は dispatch を直接 import して実行しません。`DispatchCLIPlanExecutor` が subprocess boundary で external `ai-config-dispatch` を呼びます。

- request contract: `ApprovedPlanExecutionRequest`
- result contract: `ApprovedPlanExecutionResult`
- transport: JSON file / JSON stdout
- versioning: major version compatibility (`1.x.x`)
- override: `AI_CONFIG_DISPATCH_CMD`

この形にしてあるため、dispatch は将来的に別 repo / 別 package へ移設できます。

bootstrap migration status:

- sibling repo `../ai-config-dispatch` を external runtime package bootstrap として作成済み
- local 開発では sibling checkout を優先し、deprecated in-repo shim は `AI_CONFIG_DISPATCH_ALLOW_IN_REPO_FALLBACK=1` のときだけ使う
- GCP / Cloud Run production では sibling checkout と in-repo fallback を無効化し、installed runtime か explicit override だけを許可する
- workflow assets / runtime docs / packaging / runtime package / runtime tests は external repo が正本を持つ
- `src/ai_config/dispatch/*` は deprecated import compatibility shim としてのみ残す
- cross-repo compatibility automation は `.github/workflows/dispatch-compatibility.yml` で回し、local では `bash scripts/test-dispatch-compat.sh` を使う

## Setup

```powershell
git clone https://github.com/ToshiyaTsubonishi/ai-config.git
cd ai-config
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
```

Unix-like 環境:

```bash
git clone https://github.com/ToshiyaTsubonishi/ai-config.git
cd ai-config
bash scripts/setup.sh
```

setup が行うこと:

1. 仮想環境作成
2. dependency install
3. `config/vendor_skills.yaml` の pinned ref を `skills/external` に materialize / verify
4. default profile の index build

network を避けたい場合だけ `--skip-vendor-sync` / `-SkipVendorSync` を使います。

## Register MCP

```powershell
powershell -ExecutionPolicy Bypass -File scripts/register.ps1
```

Unix-like 環境:

```bash
bash scripts/register.sh all
```

## Daily Commands

```bash
# rebuild index
ai-config-index --repo-root . --profile default

# selector MCP
ai-config-mcp-server --repo-root .

# HTTP selector surface
PORT=8080 ai-config-selector-serving --repo-root . --index-dir ./.index

# vendor observability
ai-config-vendor-skills --repo-root . status

# full doctor
ai-config-doctor --repo-root .
```

## Stable Contract

approved plan execution boundary は neutral contract module にあります。

- module: `src/ai_config/contracts/approved_plan.py`
- plan artifact: `ApprovedPlan`
- execution request: `ApprovedPlanExecutionRequest`
- execution result: `ApprovedPlanExecutionResult`

versioning policy:

- `kind` は固定 identifier
- `schema_version` は semver 風の `major.minor.patch`
- runtime は同一 major (`1.x.x`) だけ受け付ける
- `1.x` での変更は additive のみ許可し、consumer は unknown optional field を無視する
- breaking change は major を上げる

dispatch ownership policy:

- workflow assets (`workflows/*.yaml`) は dispatch repo 所有
- runtime docs / troubleshooting / packaging metadata は dispatch repo 所有
- ai-config には contracts / boundary adapter / planner integration docs を残す

## Directory Layout

```text
ai-config/
├── src/ai_config/
│   ├── contracts/       # stable plan / execution contracts
│   ├── mcp_server/      # selector MCP and selector-serving
│   ├── registry/        # ToolRecord normalization and index build
│   ├── retriever/       # hybrid retrieval / RAG
│   ├── orchestrator/    # planner library and CLI
│   ├── executor/        # tool executor and execution boundary adapters
│   ├── dispatch/        # in-repo compatibility shim
│   ├── vendor/          # external skill vendor layer
│   ├── build_index.py
│   ├── doctor.py
│   └── source_manager.py
├── config/
│   ├── master/ai-sync.yaml
│   ├── index_profiles.yaml
│   ├── sources.yaml
│   └── vendor_skills.yaml
├── docs/
├── skills/
├── workflows/
└── tests/
```

## External Skill / MCP Ownership

- `skills/external` は stable scan target のまま維持
- `config/vendor_skills.yaml` が curated vendor source の正本
- `ai-config-sources` は MCP source 管理と legacy cleanup のみ担当
- external payload の import / update / provenance は `ai-config-vendor-skills` が担当

## More Docs

- [docs/overview.md](docs/overview.md)
- [docs/architecture.md](docs/architecture.md)
- [docs/operations.md](docs/operations.md)
- [docs/development.md](docs/development.md)
- [docs/constitution.md](docs/constitution.md)
- [docs/dispatch-runtime-completion-workflow.md](docs/dispatch-runtime-completion-workflow.md)
- [docs/rename-evaluation.md](docs/rename-evaluation.md)
