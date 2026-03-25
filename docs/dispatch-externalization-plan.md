# Dispatch Externalization Plan

## Purpose

この文書は、`dispatch` を別 repo / 別 package へ切り出すための decision doc です。  
対象は次の 3 点です。

1. `ApprovedPlanExecutionResult` 1.0 contract
2. workflow assets / runtime docs / packaging の repo 帰属
3. 段階的な別 repo 化計画

## Current State

現状の前提:

- request 側 contract は `ApprovedPlanExecutionRequest` まで fixed
- `ai-config-agent execute-approved-plan` は subprocess boundary 経由で external `ai-config-dispatch` を呼ぶ
- ai-config 内の `dispatch/` は compatibility shim へ縮退した
- response 側 contract は `ApprovedPlanExecutionResult@1.0.0` で固定した
- bootstrap external repo `ai-config-dispatch` を sibling checkout として作成し、packaging / workflow assets / runtime docs / runtime package の ownership 移送を開始した

repo 依存の現状:

- runtime code: `../ai-config-dispatch/src/ai_config_dispatch/**`
- workflow assets: `../ai-config-dispatch/workflows/*.yaml`
- runtime tests: `../ai-config-dispatch/tests/test_dispatch_*`
- integration docs: `README.md`, `docs/architecture.md`, `docs/operations.md`

## Decision Summary

### 1. `ApprovedPlanExecutionResult` は ai-config core contract に置く

理由:

- ai-config 側が boundary の受け手であり、runtime を差し替えても同じ結果 contract を読める必要がある
- external runtime package が変わっても、planner / orchestration 側の呼び出しコードを固定できる

配置:

- `src/ai_config/contracts/approved_plan.py`

### 2. workflow assets は dispatch repo 所有にする

理由:

- workflow YAML は runtime の実行パターンそのもの
- DAG / retry / agent allocation と強く結合する
- ai-config core の selector / planner 責務ではない

方針:

- `workflows/*.yaml` は external dispatch repo に移す
- ai-config 側には integration test 用 fixture だけ残してよい
- ai-config docs には runtime workflow の詳細を持ち込まず、integration surface だけを書く

### 3. runtime docs は dispatch repo 所有にする

dispatch repo に置くもの:

- CLI runtime docs
- workflow authoring guide
- runtime packaging / release guide
- `.dispatch/` context handoff / retry semantics / runtime troubleshooting

ai-config に残すもの:

- `AI_CONFIG_DISPATCH_CMD` の使い方
- approved plan boundary の contract
- selector / planner から runtime を呼ぶ integration docs

### 4. packaging は dispatch repo 所有にする

dispatch repo が持つもの:

- `pyproject.toml` or packaging metadata
- `ai-config-dispatch` CLI entrypoint
- runtime dependencies (`langgraph`, workflow loader, execution runtime deps)
- release / versioning / publish pipeline

ai-config に残すもの:

- `ApprovedPlanExecutionRequest`
- `ApprovedPlanExecutionResult`
- boundary adapter (`DispatchCLIPlanExecutor`)
- optional command override (`AI_CONFIG_DISPATCH_CMD`)

## Stable Result Contract 1.0

### Contract identity

- `kind`: `ai-config.approved-plan-execution-result`
- `schema_version`: `1.0.0`

### 1.0 payload shape

```json
{
  "kind": "ai-config.approved-plan-execution-result",
  "schema_version": "1.0.0",
  "request_kind": "ai-config.approved-plan-execution-request",
  "request_schema_version": "1.0.0",
  "plan_id": "plan-123",
  "plan_revision": 2,
  "execution_id": "exec-456",
  "runtime": {
    "name": "ai-config-dispatch",
    "version": "0.1.0",
    "transport": "subprocess_json"
  },
  "status": "partial",
  "final_report": "...",
  "step_results": [
    {
      "step_id": "step-1",
      "status": "success",
      "agent": "codex",
      "tool_id": "skill:demo",
      "action": "run",
      "retry_count": 0,
      "output_summary": "...",
      "error": null
    }
  ],
  "replan_request": {
    "reason": "execution_failure"
  },
  "error": null
}
```

### Core emitted fields

- `kind`
- `schema_version`
- `request_kind`
- `request_schema_version`
- `plan_id`
- `plan_revision`
- `execution_id`
- `runtime`
- `status`
- `final_report`
- `step_results`

### Status values

- `success`
- `partial`
- `error`
- `aborted`

### Status and error semantics

- `success`: approved plan の実行が完了した状態。top-level `error=null`、`replan_request=null`、failed step result を含めない
- `partial`: 実行結果を踏まえて controlled replan が必要な状態。top-level `error=null`、`replan_request` 必須
- `error`: runtime failure または実行不能で完了できなかった状態。top-level `error` 必須、`replan_request=null`
- `aborted`: policy / operator / runtime guard により意図的に停止した状態。top-level `error` 必須、`replan_request=null`

step-level `status`:

- `success`
- `skipped`
- `error`
- `aborted`
- `timeout`

`step_results[*].error` は `error|aborted|timeout` のとき必須、`success|skipped` のとき禁止です。

### Validation rules

1. `kind` must equal `ai-config.approved-plan-execution-result`
2. `schema_version` must be `1.x.x`
3. `request_kind` / `request_schema_version` must match the executed request
4. `plan_id` / `plan_revision` must echo the request payload
5. `execution_id` must be non-empty and runtime-generated
6. `step_results[*].step_id` must be unique
7. `status=success` のとき top-level `error` は `null`
8. `status=partial` のとき `replan_request` は必須
9. `status=error|aborted` のとき `error` must be populated
10. unknown optional fields は consumer で無視してよい

### Why this shape

- ai-config 側は top-level `status` / `final_report` / `replan_request` / `step_results` だけで最小限の integration ができる
- runtime version と request echo があるため、別 repo 化後のトラブルシュートがしやすい
- timestamps や context telemetry を 1.0 必須項目に入れず、boundary を先に固定できる
- ad-hoc dict ではなく schema 化することで subprocess / package / HTTP の transport 差し替えに耐える

### Compatibility policy

- `kind` は固定 identifier とする
- `schema_version` は semver 風の `major.minor.patch` を使う
- ai-config core は `1.x.x` の result contract を受け付ける
- `2.0.0` 以上は breaking change とみなし reject する
- `1.x` では additive change のみ許可する
- consumer は unknown optional field を無視する
- required field の削除 / rename / semantic change は major version を上げる

## Repo Ownership Decision

### Keep in ai-config

- `src/ai_config/contracts/**`
- `src/ai_config/executor/plan_boundary.py`
- `src/ai_config/orchestrator/**`
- selector / planner / serving docs
- dispatch integration docs
- boundary contract tests

### Move to dispatch repo

- `src/ai_config/dispatch/**`
- `workflows/*.yaml`
- runtime-specific docs
- runtime packaging metadata
- runtime release pipeline
- runtime-only tests

### Bootstrap implementation status

- done: external repo `ai-config-dispatch` を作成
- done: workflow assets / runtime docs / packaging metadata を external repo に配置
- done: runtime package `ai_config_dispatch` を external repo に配置
- done: ai-config boundary adapter が sibling external repo を優先解決
- transitional: shared contracts / executor / runtime env helper は `ai-config` package に依存
- next: ai-config から in-repo compatibility shim をさらに薄くし、external package を主系にする

### Transitional / shared

- integration tests that verify boundary compatibility can remain in ai-config
- fixture workflows for tests may be copied into both repos temporarily
- docs cross-linking is acceptable during migration

## Migration Plan

### Phase 1: Freeze result contract

Deliverables:

- `ApprovedPlanExecutionResult` model
- JSON schema export
- contract tests
- `DispatchCLIPlanExecutor` updated to parse the result model instead of loose dict

Acceptance:

- ai-config can reject malformed runtime results before using them
- runtime returns `kind` / `schema_version` / `execution_id`
- status / error semantics and request echo are validated at the boundary

### Phase 2: Split ownership in-place

Deliverables:

- docs that mark workflow assets / runtime docs / packaging as dispatch-owned
- dispatch repo skeleton directory plan
- runtime-only docs removed from ai-config or replaced with links

Acceptance:

- ai-config docs describe integration only
- dispatch-owned assets are enumerated explicitly

### Phase 3: Create external dispatch repo

Deliverables:

- new repo with package metadata
- copied `dispatch/` runtime code
- copied `workflows/`
- runtime docs and release instructions

Acceptance:

- external repo can build and run `ai-config-dispatch`
- ai-config still works with `AI_CONFIG_DISPATCH_CMD`

### Phase 4: Switch ai-config integration to external package by default

Deliverables:

- boundary adapter default command resolution updated for external package path or installed binary
- CI path validating external runtime integration
- ai-config tree no longer imports or packages runtime internals

Acceptance:

- ai-config can operate without local `src/ai_config/dispatch/**`
- only the stable contracts and boundary adapter remain in ai-config

### Phase 5: Remove compatibility shim from ai-config

Deliverables:

- delete in-repo runtime implementation
- retain contract tests and external integration smoke tests
- final docs cleanup

Acceptance:

- ai-config remains a selector / planner platform
- dispatch release cadence is decoupled

## File Move Proposal

### From ai-config to dispatch repo

```text
src/ai_config/dispatch/
workflows/
tests/test_dispatch_*.py
```

### Stay in ai-config

```text
src/ai_config/contracts/
src/ai_config/executor/plan_boundary.py
src/ai_config/orchestrator/
tests/test_plan_boundary.py
tests/test_approved_plan_contract.py
```

## Risks

- response schema を急ぎすぎると runtime の内部情報を top-level に漏らしすぎる
- workflow assets を移すと test fixture path が壊れやすい
- external package 名や release channel を先に決めないと `AI_CONFIG_DISPATCH_CMD` 依存が長引く
- in-repo runtime を消す前に CI で external runtime integration を固定する必要がある

## Recommended Next Implementation Slice

最小の次スライス:

1. `ApprovedPlanExecutionResult` を contract module に追加
2. dispatch CLI の `--json` 出力を stable schema に変更
3. `DispatchCLIPlanExecutor` を result model ベースに更新
4. docs に ownership decisions を反映

この 4 点が終われば、repo 分離の前提がかなり固まります。
