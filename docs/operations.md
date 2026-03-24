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

### 環境変数

```bash
# planner LLM
GOOGLE_API_KEY=...

# optional runtime command overrides
AI_CONFIG_GEMINI_CMD=gemini
AI_CONFIG_CODEX_CMD=codex
AI_CONFIG_ANTIGRAVITY_CMD=antigravity
AI_CONFIG_DISPATCH_CMD=/path/to/external/ai-config-dispatch
```

`AI_CONFIG_DISPATCH_CMD` は、dispatch runtime を別 repo / 別 package に出した後も `ai-config-agent` 側を変えずに接続先だけ差し替えるための override です。

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

## Dispatch Runtime

`ai-config-dispatch` は execution runtime として扱います。

### Prompt-based runtime

```bash
ai-config-dispatch "バグを修正してテストを実行して"
ai-config-dispatch "テスト実行" --parallel
ai-config-dispatch --list-workflows
```

### Approved plan execution runtime

```bash
ai-config-dispatch --execute-approved-plan ./approved-plan-request.json --json
```

この入口は ai-config core から見た stable runtime boundary です。
repo 内には compatibility 実装がありますが、将来的には external runtime に置き換える前提です。

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

ownership decision:

- workflow assets は dispatch repo 所有
- runtime docs / packaging metadata は dispatch repo 所有
- ai-config docs は contract と integration surface のみ持つ

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
