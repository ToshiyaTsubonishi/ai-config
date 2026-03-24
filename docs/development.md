# ai-config 開発者ガイド

## Development Priorities

この repo で優先する順序:

1. selector / retrieval quality
2. runtime validation and serving stability
3. planner artifact quality
4. dispatch runtime externalization

planner や dispatch runtime を触るときも、`ai-config` の中核責務は selector platform であることを前提にします。

## Project Structure

```text
src/ai_config/
├── contracts/       # ApprovedPlan / ApprovedPlanExecutionRequest
├── registry/        # ToolRecord normalization and index build
├── retriever/       # hybrid retrieval / RAG
├── mcp_server/      # selector MCP and selector-serving
├── orchestrator/    # planner library and planner-facing CLI
├── executor/        # local tool executor and dispatch boundary adapter
├── dispatch/        # compatibility runtime; separate-repo candidate
├── vendor/          # import / provenance / manifest ownership
├── doctor.py
├── build_index.py
└── source_manager.py
```

## Architectural Rules

### 1. Contracts live outside orchestrator and dispatch

stable boundary models は `contracts/approved_plan.py` に置きます。

- `ApprovedPlan`
- `ApprovedPlanExecutionRequest`
- JSON schema export helpers
- structural validation

`dispatch/` が contract を使うのはよいですが、`dispatch/` から `orchestrator/` を import してはいけません。

### 2. Orchestrator is planner-first

`orchestrator/` の標準責務:

- candidate retrieval
- plan artifact generation
- plan validation
- controlled replan

`orchestrator/cli.py` は `dispatch` を import しません。実行が必要なときは `executor/plan_boundary.py` を通します。

### 3. Execution uses boundary adapters

dispatch runtime への接続は `DispatchCLIPlanExecutor` が担います。

現在の transport:

- request: JSON file
- response: JSON stdout
- command: `python -m ai_config.dispatch.cli --execute-approved-plan ... --json`

将来 HTTP や external package に変えても、planner 側の public surface は変えない前提です。

### 4. Selector-serving is first-class

deploy や runtime observability を追加するときは、まず `ai-config-selector-serving` を起点に考えます。

## Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,semantic]"
```

### Typical Loop

```bash
ai-config-vendor-skills --repo-root . sync-manifest
ai-config-index --repo-root . --profile default
ai-config-agent search "selector serving"
```

## CLI Surfaces for Developers

```bash
# planner surfaces
python -m ai_config.orchestrator.cli search "eslint"
python -m ai_config.orchestrator.cli plan "codex で修正"
python -m ai_config.orchestrator.cli execute-approved-plan --plan ./approved-plan.json

# runtime surface
python -m ai_config.dispatch.cli --execute-approved-plan ./approved-plan-request.json --json

# serving surface
python -m ai_config.mcp_server.serving --repo-root . --index-dir ./.index
```

## Testing

### Focused suites

```bash
.venv/bin/python -m pytest tests/test_approved_plan_contract.py -q
.venv/bin/python -m pytest tests/test_plan_boundary.py -q
.venv/bin/python -m pytest tests/test_cli_smoke.py -q
.venv/bin/python -m pytest tests/test_selector_serving.py -q
```

### Planner / runtime regression

```bash
.venv/bin/python -m pytest \
  tests/test_dispatch_approved_plan.py \
  tests/test_dispatch_planner.py \
  tests/test_orchestrator_plan_artifacts.py \
  tests/test_selector_serving.py -q
```

### Full suite

```bash
.venv/bin/python -m pytest tests/ -q
```

## Current Test Map

| Test file | Purpose |
|---|---|
| `test_approved_plan_contract.py` | stable contract defaults / schema / validation |
| `test_plan_boundary.py` | subprocess execution boundary |
| `test_cli_smoke.py` | planner CLI search / plan / execute surfaces |
| `test_dispatch_approved_plan.py` | approved plan execution runtime |
| `test_dispatch_planner.py` | prompt-to-plan runtime behavior |
| `test_orchestrator_plan_artifacts.py` | planner artifact generation and validation |
| `test_selector_serving.py` | selector-serving HTTP / readiness / fail-fast |

## Extending the System

### Add a new selector-facing parser

1. update `registry/`
2. normalize to `ToolRecord`
3. add index / retrieval tests
4. avoid coupling parser logic to dispatch runtime

### Add a new planner behavior

1. prefer `OrchestrationPlanner` public methods
2. keep changes inside artifact generation / validation / controlled replan
3. do not make planner responsible for runtime scheduling

### Change dispatch integration

1. preserve `ApprovedPlanExecutionRequest`
2. preserve major-version compatibility
3. change only `executor/plan_boundary.py`

## Notes on Legacy Paths

- `orchestrator/plan_schema.py` と `orchestrator/validator.py` は compatibility wrapper
- `dispatch/` は repo 内 compatibility runtime
- legacy flag CLI は移行期間の互換経路

新規実装では neutral contract module と subcommand CLI を優先してください。
