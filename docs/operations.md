# ai-config 運用ガイド

## Operating Model

日常運用では次の順序を標準にします。

1. vendor state を整える
2. index を build する
3. selector surface を使う
4. 必要時だけ plan artifact を作る
5. approved plan の実行は boundary 越しに dispatch runtime へ渡す

## Setup

### 前提条件

- Python 3.11+
- Git
- Claude Code / Codex / Gemini CLI / Antigravity のいずれか

### 初回セットアップ

```powershell
git clone https://github.com/ToshiyaTsubonishi/ai-config.git
cd ai-config
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
```

Unix-like:

```bash
git clone https://github.com/ToshiyaTsubonishi/ai-config.git
cd ai-config
bash scripts/setup.sh
```

setup の内容:

1. 仮想環境作成
2. dependency install
3. `config/vendor_skills.yaml` の pinned ref を `skills/external` に materialize / verify
4. default profile で `.index` build

`skills.sh official` snapshot は opt-in です。repo 数が多いため setup では同期しません。

### 環境変数

```bash
# planner LLM
GOOGLE_API_KEY=...

# optional runtime command overrides
AI_CONFIG_GEMINI_CMD=gemini
AI_CONFIG_CODEX_CMD=codex
AI_CONFIG_ANTIGRAVITY_CMD=antigravity
AI_CONFIG_DISPATCH_CMD=/path/to/external/ai-config-dispatch
AI_CONFIG_DISPATCH_RUNTIME_MODE=auto
```

`AI_CONFIG_DISPATCH_CMD` は、dispatch runtime を別 repo / 別 package に出した後も `ai-config-agent` 側を変えずに接続先だけ差し替えるための override です。

`AI_CONFIG_DISPATCH_RUNTIME_MODE`:

- `auto`: デフォルト。Cloud Run 系 env があれば production、それ以外は local
- `local`: sibling checkout を含む開発用解決順を使う
- `production`: sibling checkout を禁止し、installed runtime だけを使う

## MCP Registration

```powershell
powershell -ExecutionPolicy Bypass -File scripts/register.ps1
```

Unix-like:

```bash
bash scripts/register.sh all
```

登録後、`ai-config-selector` MCP が使えるようになります。

## Daily Operation

### 1. Vendor State

```bash
ai-config-vendor-skills --repo-root . status
ai-config-vendor-skills --repo-root . sync-manifest
```

ポイント:

- `config/vendor_skills.yaml` が正本
- `skills/external` は scan target
- `status` は local-only / network-free

### 1b. Optional `skills.sh official` Snapshot

```bash
ai-config-vendor-skills --repo-root . refresh-skills-sh-official-manifest
ai-config-vendor-skills --repo-root . sync-skills-sh-official
```

ポイント:

- `config/skills_sh_official.yaml` は `https://skills.sh/official` から解決できた public repo の pinned snapshot
- `config/skills_sh_official_skipped.json` には private / missing repo を残す
- payload は `skills/official` に materialize される
- `skills/official` は `skills/imported` / `skills/external` より先に dedup されるので、完全重複 skill id は official 側が勝つ

### 2. Build Index

```bash
ai-config-index --repo-root . --profile default
ai-config-index --repo-root . --profile full
ai-config-index --repo-root . --profile default --watch
```

### 3. Selector Surfaces

stdio MCP:

```bash
ai-config-mcp-server --repo-root .
```

HTTP deploy surface:

```bash
PORT=8080 ai-config-selector-serving --repo-root . --index-dir ./.index
```

selector-serving readiness payload には次が含まれます。

- `surface=selector-serving`
- `runtime_mode=read_only`
- `record_count`
- `index_format_version`
- `required_artifacts`

### 4. Search and Plan

```bash
# search only
ai-config-agent search "eslint config" --index-dir ./.index

# plan only
ai-config-agent plan "codex でバグを修正" --index-dir ./.index

# schema inspection
ai-config-agent schema approved-plan
ai-config-agent schema approved-plan-execution-request
ai-config-agent schema approved-plan-execution-result
```

### 5. Execute Approved Plan

```bash
ai-config-agent execute-approved-plan --plan ./approved-plan.json --index-dir ./.index
```

このコマンドは dispatch runtime を直接 import しません。`ApprovedPlanExecutionRequest` を作り、stable boundary 経由で runtime に渡します。

互換のため、従来の `--execute-plan` も当面使えます。

## External Runtime Connection

`ai-config-dispatch` は execution runtime として扱います。

runtime CLI / workflow / packaging / release docs は `ai-config-dispatch` repo を正本にしてください。`ai-config` 側には approved-plan boundary の接続方法だけを残します。

### Boundary invocation

```bash
ai-config-dispatch --execute-approved-plan ./approved-plan-request.json --json
```

この入口は ai-config core から見た stable runtime boundary です。repo 内には runnable runtime は残っていません。

local mode:

1. `AI_CONFIG_DISPATCH_CMD`
2. sibling repo `../ai-config-dispatch`
3. installed `ai-config-dispatch`
4. installed `python -m ai_config_dispatch.cli`
5. fail fast

GCP / Cloud Run production mode:

1. `AI_CONFIG_DISPATCH_CMD`
2. installed `ai-config-dispatch`
3. in-image `python -m ai_config_dispatch.cli`
4. fail fast

`--json` の stable payload:

- `kind=ai-config.approved-plan-execution-result`
- `schema_version=1.0.0`
- `status=success|partial|error|aborted`
- `error` は `error|aborted` のとき必須
- `partial` は `replan_request` を返す
- `plan_id` / `plan_revision` / request echo は input request と一致する

CLI exit policy:

- `success` / `partial`: exit 0
- `error` / `aborted`: exit 1

## Health and Readiness

### selector-serving

```bash
curl http://127.0.0.1:8080/healthz
curl http://127.0.0.1:8080/readyz
```

期待:

- `/healthz`: process liveness
- `/readyz`: index contract が有効で selector read surface が公開可能

### Doctor

```bash
ai-config-doctor --repo-root .
```

包括診断の対象:

- vendor manifest / materialization
- index presence
- selector MCP reachability
- downstream MCP catalog / tool list / tool call
- dispatch runtime resolution (`local` / `production`, selected source)

GCP / Cloud Run production では次を推奨します。

```bash
AI_CONFIG_DISPATCH_RUNTIME_MODE=production ai-config-doctor --repo-root .
```

### Cross-repo compatibility smoke

```bash
bash scripts/test-dispatch-compat.sh
```

GitHub Actions:

- workflow: `.github/workflows/dispatch-compatibility.yml`
- default track: `ai-config-dispatch@main`
- optional stable track: repo variable `AI_CONFIG_DISPATCH_STABLE_REF` または `workflow_dispatch` input

required check policy:

- `ai-config` の protected `main` では job `ai-config vs ai-config-dispatch@main` を required check にする
- `ai-config-dispatch` の protected `main` では job `ai-config-dispatch vs ai-config@main` を required check にする
- `compat-stable` job は repo variable / `workflow_dispatch` input があるときだけ出る conditional job なので、required にはしない

stable track policy:

- release tag が無い間は `AI_CONFIG_DISPATCH_STABLE_REF` / `AI_CONFIG_STABLE_REF` に branch 名ではなく exact commit SHA を入れる
- stable ref を進める前に main track の compatibility workflow と local smoke を green にする
- stable ref を更新したら、両 repo で `workflow_dispatch` を 1 回ずつ実行して stable track の green run を残す
- 手元で GitHub auth が無い場合は local smoke を先に回し、authenticated な環境で `workflow_dispatch` を実行する

## Troubleshooting

### `.index` がない / 壊れている

```bash
ai-config-index --repo-root . --profile default
```

### selector-serving が起動しない

主な原因:

- required artifact 不足
- `index_format_version` mismatch
- build-time materialization 未完了

runtime では `sync-manifest` や `ai-config-index` を自動実行しません。build pipeline 側で直します。

### approved plan execution が失敗する

確認順:

1. `ai-config-agent schema approved-plan-execution-request` で contract を確認する
2. approved plan の `tool_id` が index 上の record と一致するか確認する
3. `AI_CONFIG_DISPATCH_CMD` が外部 runtime を指していないか確認する
4. `ai-config-dispatch --execute-approved-plan ... --json` を直接叩いて境界の外側を切り分ける

GCP / Cloud Run production 追加確認:

1. `AI_CONFIG_DISPATCH_RUNTIME_MODE=production` を設定する
2. image に `ai-config-dispatch` package か `python -m ai_config_dispatch.cli` 実行環境があることを確認する
3. `ai-config-doctor --repo-root .` の `dispatch_resolution` が `installed_binary` か `installed_module` になっていることを確認する

ownership decision:

- workflow assets は dispatch repo 所有
- runtime docs / packaging metadata は dispatch repo 所有
- ai-config docs は contract と integration surface のみ持つ
- ai-config package の `dispatch/` は import guard のみ残す

## Migration Notes

移行期間の互換経路:

- `ai-config-agent --search-only`
- `ai-config-agent --plan-only`
- `ai-config-agent --execute-plan`

新規運用では次の surface を優先します。

- `ai-config-agent search`
- `ai-config-agent plan`
- `ai-config-agent execute-approved-plan`
- `ai-config-selector-serving`

dispatch 別 repo 化の段階計画、`ApprovedPlanExecutionResult@1.0.0`、ownership decision は `docs/dispatch-externalization-plan.md` を参照してください。
