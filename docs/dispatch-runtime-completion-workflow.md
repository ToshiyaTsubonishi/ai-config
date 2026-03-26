# Dispatch Runtime Completion Workflow

## Purpose

この文書は、`dispatch` 分離の次フェーズを **実行順序つきの workflow** として固定するための運用ドキュメントです。

進行順は固定です。

1. `ai-config-dispatch` に runtime を寄せ切る
2. GCP 本番向けに command 解決順序を production-safe にする
3. 両 repo の互換テストを自動化する
4. その後で `ai-config` rename を検討する

この順序を崩さない理由:

- rename を先に始めると、runtime 分離の不具合と naming 変更の影響が混ざる
- GCP 本番の command 解決を後回しにすると、local dev 用 fallback が本番に混入する
- 互換テスト自動化なしで rename に入ると、repo 間の境界 regressions を見落としやすい

## Non-goals

- selector / planner の既存責務を再拡張しない
- build-time index / read-only runtime 前提を崩さない
- `skills/external` と `config/vendor_skills.yaml` の ownership を変更しない
- Phase 1-3 完了前に package / repo / CLI rename を始めない

## Phase Overview

| Phase | Goal | Primary Repo | Exit Gate |
|---|---|---|---|
| 1 | runtime 所有物を `ai-config-dispatch` に寄せ切る | `ai-config-dispatch` | `ai-config` に runnable runtime 実装が残らない |
| 2 | GCP 本番で安全な command 解決にする | `ai-config` | production mode で sibling / in-repo fallback が無効 |
| 3 | repo 間互換テストを自動化する | both | push / PR で boundary 回帰が検出できる |
| 4 | rename の是非と範囲を評価する | `ai-config` | decision memo が出てから rename 可否を判断 |

## Phase 1: Runtime Cutover To `ai-config-dispatch`

### Objective

`approved plan` 実行 runtime の正本を `ai-config-dispatch` に完全に寄せ、`ai-config` には selector / planner / contract / boundary だけを残します。

### Current dependencies to resolve

現状、external runtime はまだ次の shared import を持っています。

- `ai_config.contracts.approved_plan`
- `ai_config.executor.ToolExecutor`
- `ai_config.runtime_env.load_runtime_env`
- test-only import としての `ai_config.orchestrator.plan_schema`
- test-only import としての `ai_config.registry.models`

この phase では「runtime 実装を外へ寄せ切る」ことが目的です。  
shared contract / executor API への依存は許容しますが、`dispatch` runtime の内部実装が `ai-config` repo に残る状態は解消します。

### Work items

1. `ai-config` 側の `src/ai_config/dispatch/*` を deprecation shim か import guard まで縮退する
2. runtime-only docs / tests / workflow assets / packaging metadata の正本を `ai-config-dispatch` に一本化する
3. external repo の tests から `ai-config` 内部実装型への依存を減らし、contract / fixture ベースへ寄せる
4. `ai-config-dispatch` から使う shared API を `contract` / `executor` / `runtime_env` に限定し、内部 import を増やさない
5. `ai-config` docs から runtime 実装説明を外し、boundary と integration に寄せる

### Deliverables

- `ai-config-dispatch` が runtime package / workflow / runtime docs / runtime tests の唯一の正本になる
- `ai-config` の `dispatch` は compatibility layer か、明示 deprecation のみを残す
- 両 repo の ownership 説明が docs で一致する

### Validation

```bash
# ai-config
PYTHONPATH=src .venv/bin/python -m pytest \
  tests/test_approved_plan_contract.py \
  tests/test_plan_boundary.py \
  tests/test_dispatch_compat_shim.py \
  tests/test_cli_smoke.py -q

# ai-config-dispatch
PYTHONPATH=../ai-config/src:src ../ai-config/.venv/bin/python -m pytest -q

rg -n "from ai_config\\.dispatch|ai_config\\.dispatch\\." src tests
```

### Exit gate

- `ai-config` に runtime-only test が残っていない
- `ai-config-dispatch` が runtime package の正本として単独で説明できる
- `ai-config` 側は boundary adapter と compatibility entry 以外で `dispatch` runtime を抱えない

## Phase 2: Production-safe Command Resolution For GCP

### Objective

GCP 本番では local development 用 fallback を無効にし、明示的で再現可能な command 解決だけを許可します。

### Target resolution matrix

| Environment | Allowed order | Forbidden |
|---|---|---|
| local dev | `AI_CONFIG_DISPATCH_CMD` -> sibling checkout -> installed `ai-config-dispatch` -> explicit compat fallback | silent hard failure without diagnostics |
| GCP production | `AI_CONFIG_DISPATCH_CMD` -> installed `ai-config-dispatch` -> in-image `python -m ai_config_dispatch.cli` -> fail fast | sibling checkout, implicit in-repo shim |

### Production rules

- Cloud Run / GCP production では sibling checkout を探索しない
- in-repo compatibility runtime は production mode では使わない
- runtime が未インストールなら startup か first-call で fail-fast する
- production / local の判定は implicit heuristic だけに頼らず、明示 env でも固定できるようにする

### Work items

1. `DispatchCLIPlanExecutor` に runtime mode を導入する
2. GCP production 判定と local dev 判定の resolution matrix を unit test 化する
3. Cloud Run / GCP deploy docs に required env / startup check / failure mode を明記する
4. in-repo fallback は `AI_CONFIG_DISPATCH_ALLOW_IN_REPO_FALLBACK=1` のような明示 opt-in に閉じ込める

### Deliverables

- production-safe な command resolution policy
- GCP deploy docs と readiness / doctor の確認手順
- resolution matrix を検証する unit tests

### Validation

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_plan_boundary.py -q
PYTHONPATH=src .venv/bin/python -m ai_config.orchestrator.cli schema approved-plan-execution-request
PYTHONPATH=src .venv/bin/python -m ai_config.orchestrator.cli schema approved-plan-execution-result
```

### Exit gate

- GCP production 相当 env で sibling / in-repo fallback が選ばれない
- runtime 未導入時は明示エラーになる
- local dev では既存の作業性を大きく落とさない

## Phase 3: Cross-repo Compatibility Automation

### Objective

`ai-config` と `ai-config-dispatch` の boundary regressions を push / PR / scheduled run で自動検出できるようにします。

### Work items

1. `ai-config` 側に external dispatch を組み込んだ compatibility job を追加する
2. `ai-config-dispatch` 側に current `ai-config` main もしくは release を使う compatibility job を追加する
3. shared fixture を `ApprovedPlanExecutionRequest` / `ApprovedPlanExecutionResult` 中心で固定する
4. main-to-main と release-to-main の少なくとも 2 系統を自動実行する
5. 契約破壊と runtime failure をログ上で切り分けられるようにする

### Deliverables

- 両 repo の CI に compatibility checks が入る
- shared fixture と validation command が docs 化される
- repo 片側だけの変更でも boundary break を検出できる

### Validation

```bash
# local compatibility smoke
PYTHONPATH=src .venv/bin/python -m pytest tests/test_plan_boundary.py tests/test_dispatch_compat_shim.py -q
PYTHONPATH=../ai-config/src:src ../ai-config/.venv/bin/python -m pytest tests/test_dispatch_cli_result_contract.py tests/test_dispatch_approved_plan.py -q
bash scripts/test-dispatch-compat.sh
bash ../ai-config-dispatch/scripts/test-ai-config-compat.sh
```

GitHub Actions:

- `ai-config/.github/workflows/dispatch-compatibility.yml`
- `ai-config-dispatch/.github/workflows/ai-config-compatibility.yml`

optional stable track:

- `ai-config` repo variable: `AI_CONFIG_DISPATCH_STABLE_REF`
- `ai-config-dispatch` repo variable: `AI_CONFIG_STABLE_REF`
- どちらも `workflow_dispatch` input で一時上書き可能

### Exit gate

- `ai-config` push で external dispatch 互換が検証される
- `ai-config-dispatch` push で current `ai-config` 互換が検証される
- shared contract change の破壊が CI で検知できる

## Phase 4: Rename Evaluation

### Objective

runtime 分離と compatibility automation が安定したあとで、`ai-config` rename の必要性とコストを判断します。  
この phase は **評価のみ** です。rename 実施は別決定にします。

### Preconditions

- Phase 1-3 の exit gate がすべて green
- external dispatch repo の ownership が安定している
- GCP production-safe path が本番前提で説明できる

### Work items

1. rename 候補と非候補を整理する
2. package 名 / CLI 名 / env 名 / repo 名 / docs / import path への影響を棚卸しする
3. backward compatibility window と deprecation strategy を見積もる
4. rename しない場合の説明コストも比較する

### Deliverables

- rename decision memo
- naming option ごとの impact matrix
- 実施するなら separate migration plan、見送るなら rationale

結果は [Rename Evaluation](rename-evaluation.md) に記録します。

### Exit gate

- rename の是非が文書化されている
- rename 実施前に必要な compatibility window が明確
- selector platform と dispatch runtime の責務説明が崩れない

## Recommended Execution Mode

`ai-config-dispatch` 側の predefined workflow `dispatch-runtime-completion` を使って着手してよいです。  
ただし、この workflow doc が正本です。workflow YAML は実行補助として扱います。

## Completion Criteria

この workflow は次を満たした時点で完了です。

- `ai-config-dispatch` が runtime 正本として説明・配布・検証できる
- GCP 本番で fallback 混入のない command resolution が固定される
- 両 repo 間の compatibility regressions を CI で検出できる
- rename は独立した意思決定として扱われ、前段の移行品質と混ざらない
