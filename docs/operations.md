# ai-config 運用ガイド

## セットアップ

### 前提条件

- **Python 3.11 以上**
- **Git**（外部ソース管理に必要）
- AI ツール（Claude Code / Codex / Antigravity / Gemini CLI）のいずれか

### 初回セットアップ

```powershell
git clone https://github.com/ToshiyaTsubonishi/ai-config.git
cd ai-config
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
```

`scripts/setup.ps1` / `scripts/setup.sh` は以下を行います:
1. Python 仮想環境（`.venv`）の作成
2. 依存パッケージのインストール
3. `config/vendor_skills.yaml` の exact ref を `skills/external` に materialize / verify
4. `.env.example` を `.env` にコピー（初回のみ、Windows）
5. default index を構築

vendor sync が不要、または network 依存を明示的に避けたい場合のみ `bash scripts/setup.sh --skip-vendor-sync` / `powershell ... -SkipVendorSync` を使います。その場合は external skill coverage が baseline と一致しない可能性があります。

### 環境変数の設定

`.env` ファイルを編集して必要な API キーを設定します:

```bash
# 必須: オーケストレーター・ディスパッチのプランニング LLM 用
GOOGLE_API_KEY=your-google-api-key

# オプション: GitHub MCP 用
GITHUB_PERSONAL_ACCESS_TOKEN=your-github-pat

# オプション: CLI コマンドのカスタマイズ
AI_CONFIG_GEMINI_CMD=gemini
AI_CONFIG_CODEX_CMD=codex
AI_CONFIG_ANTIGRAVITY_CMD=antigravity
```

> ⚠️ `.env` はコミットしないでください（`.gitignore` 対象です）

### AI ツールへの登録

```powershell
# 全ツールに一括登録
powershell -ExecutionPolicy Bypass -File scripts/register.ps1

# 個別登録
powershell -ExecutionPolicy Bypass -File scripts/register.ps1 antigravity
powershell -ExecutionPolicy Bypass -File scripts/register.ps1 gemini_cli
powershell -ExecutionPolicy Bypass -File scripts/register.ps1 codex
```

登録後、各 AI ツールから `ai-config-selector` の 4 つのツール（`search_tools` / `get_tool_detail` / `list_categories` / `get_tool_count`）が利用可能になります。

---

## 日常運用

### インデックスの構築

スキルや MCP サーバーの追加・変更後、インデックスを再構築します。

```bash
# 通常ビルド（default プロファイル）
ai-config-index --repo-root . --profile default

# 全件ビルド
ai-config-index --repo-root . --profile full

# ファイル変更を監視して自動リビルド（開発中に便利）
ai-config-index --repo-root . --profile default --watch
```

#### インデックスプロファイル

`config/index_profiles.yaml` で定義されたプロファイルにより、対象を制御できます。

| プロファイル | 内容 |
|---|---|
| `default` | 通常運用向け（大規模スキルセットを除外） |
| `full` | すべてのスキル・MCP を収録 |

### 外部 skill の vendor layer 管理

```bash
# local-only / network-free の vendor state 確認
ai-config-vendor-skills --repo-root . status

# machine-readable status
ai-config-vendor-skills --repo-root . status --json

# pinned manifest を materialize / verify
ai-config-vendor-skills --repo-root . sync-manifest

# manifest にない vendor-managed dir を明示的に prune
ai-config-vendor-skills --repo-root . sync-manifest --prune --dry-run
ai-config-vendor-skills --repo-root . sync-manifest --prune

# skill repo の import
ai-config-vendor-skills --repo-root . import user/skills my-skills --ref <commit-or-tag>

# provenance に基づく update
ai-config-vendor-skills --repo-root . update --all

# vendor-managed checkout の remove
ai-config-vendor-skills --repo-root . remove my-skills
```

`config/vendor_skills.yaml` に commit される curated entry では `ref` が必須です。branch head を勝手に追う運用にはしません。

`bootstrap-legacy` と `cleanup-legacy-submodule` は migration utility です。既存 submodule / checkout へ `.import.json` を backfill し、legacy gitlink を local artifact に変換するための一時的な経路であり、日常運用の中心にはしません。

### Vendor observability

```bash
# 日常確認: vendor layer だけを見る
ai-config-vendor-skills --repo-root . status

# JSON 出力: schema_version / generated_at を含む安定 schema
ai-config-vendor-skills --repo-root . status --json

# 包括診断: vendor / setup / index / selector をまとめて確認
ai-config-doctor --repo-root .
```

使い分け:

- `ai-config-vendor-skills status`: local-only / non-destructive / network-free な vendor state の確認
- `ai-config-doctor`: vendor manifest / materialization / git hygiene / index presence を含む包括診断

判定方針:

- `extra_local` は pass with details
- `unmanaged_local` は provenance 不在の unmanaged content として fail

`unmanaged_local` は drift / shadowing / accidental local residue の可能性があるため、warning ではなく失敗として扱います。

### Legacy cleanup safety

```bash
# 1. single repo dry-run
ai-config-vendor-skills --repo-root . cleanup-legacy-submodule remotion

# 2. same repo apply
ai-config-vendor-skills --repo-root . cleanup-legacy-submodule remotion --apply

# 3. verify index / selector / git state

# 4. all dry-run
ai-config-vendor-skills --repo-root . cleanup-legacy-submodule --all

# 5. all apply
ai-config-vendor-skills --repo-root . cleanup-legacy-submodule --all --apply
```

cleanup は provenance 未確立 path を処理しません。標準は preview-only で、`--apply` があるときだけ mutation します。

### MCP source と legacy config cleanup

```bash
# ソース一覧の確認
ai-config-sources --repo-root . list

# MCP source の同期
ai-config-sources --repo-root . sync

# 事前確認（変更は行わない）
ai-config-sources --repo-root . sync --dry-run

# 新しい MCP source の追加
ai-config-sources --repo-root . add my-mcp https://github.com/user/mcp-server.git --type mcp

# MCP source または legacy manifest entry の削除
ai-config-sources --repo-root . remove my-mcp
```

### 推奨ワークフロー（ソース更新後）

```bash
ai-config-vendor-skills --repo-root . sync-manifest
ai-config-sources --repo-root . sync
ai-config-index --repo-root . --profile default
```

---

## CLI ツール一覧

### `ai-config-index` — インデックス構築

```bash
ai-config-index --repo-root . [--profile default] [--watch]
```

| オプション | 説明 | デフォルト |
|---|---|---|
| `--repo-root` | リポジトリルート | `.` |
| `--index-dir` | インデックス出力先 | `.index` |
| `--profile` | プロファイル名 | `default` |
| `--watch` | ファイル変更の自動検出 | off |
| `--embedding-backend` | `hash` or `sentence_transformer` | `hash` |
| `--vector-backend` | `numpy` or `faiss` | `numpy` |

### `ai-config-mcp-server` — MCP サーバー起動

```bash
ai-config-mcp-server --repo-root .
```

> 通常は AI ツールが自動起動するため、手動起動は不要です。

HTTP transport で起動する場合:

```bash
ai-config-mcp-server \
  --repo-root . \
  --transport streamable-http \
  --host 127.0.0.1 \
  --port 8000 \
  --streamable-http-path /mcp
```

### `ai-config-selector-serving` — Cloud Run selector-serving target

```bash
PORT=8080 ai-config-selector-serving --repo-root . --index-dir ./.index
```

- transport は `streamable-http` 固定です
- MCP endpoint は `/mcp`
- liveness は `/healthz`
- readiness は `/readyz`
- runtime では `sync-manifest` / `ai-config-index` を実行しません
- `.index` の required artifacts が不足している場合は fail-fast で起動失敗します

Cloud Run image build では `skills/external` の materialization と `.index` build を完了させてから runtime に渡します。runtime は `skills/`、`config/`、`.index/` を read-only に使うだけです。

### `ai-config-agent` — オーケストレーター

```bash
# 検索のみ
ai-config-agent "ESLint の設定を確認したい" --search-only

# plan のみ生成
ai-config-agent "codex で実行して" --top-k 8 --plan-only

# plan 作成 → 実行
ai-config-agent "codex で実行して" --top-k 8 --max-retries 2 --max-replans 2

# 承認済み plan の実行
ai-config-agent --index-dir .index --execute-plan ./approved-plan.json
```

| オプション | 説明 | デフォルト |
|---|---|---|
| `--search-only` | 検索結果の表示のみ | off |
| `--plan-only` | 構造化 plan のみ表示 | off |
| `--execute-plan` | 承認済み JSON plan を実行 | なし |
| `--top-k` | 検索結果の最大件数 | `8` |
| `--max-retries` | plan 実行時の各ステップ最大リトライ | `2` |
| `--max-replans` | 制御された再計画の最大回数 | `2` |
| `--parallel` | 依存のない承認済み step を並列実行 | off |
| `--keep-context` | `.dispatch/` の実行コンテキストを保持 | off |
| `--trace` | JSON 実行トレース出力 | off |

#### `plan-only` 出力例

```text
Plan ID: plan-abc123 (rev 1)
Goal: codex で実行して
Specialist: software_engineering
Feasibility: partial
Approval required: yes

Steps:
- step-1: Use codex -> toolchain:codex (depends_on=none)
  expected: Initial execution result from toolchain:codex
```

#### 承認済み plan JSON 例

```json
{
  "plan_id": "plan-cli",
  "revision": 1,
  "user_goal": "Open the demo skill",
  "assumptions": [],
  "specialist_route": "general",
  "candidate_tools": [
    {
      "tool_id": "skill:demo-skill",
      "tool_kind": "skill",
      "name": "demo-skill",
      "source_path": "skills/shared/demo/SKILL.md",
      "selection_reason": "approved",
      "invoke_summary": "skill_markdown: skills/shared/demo/SKILL.md",
      "confidence": 0.8
    }
  ],
  "steps": [
    {
      "step_id": "step-1",
      "title": "Open demo",
      "purpose": "Read the demo skill",
      "inputs": ["demo"],
      "expected_output": "content preview",
      "tool_ref": {
        "tool_id": "skill:demo-skill",
        "tool_kind": "skill",
        "name": "demo-skill",
        "source_path": "skills/shared/demo/SKILL.md",
        "selection_reason": "approved",
        "invoke_summary": "skill_markdown: skills/shared/demo/SKILL.md",
        "confidence": 0.8
      },
      "depends_on": [],
      "fallback_strategy": {
        "action": "abort",
        "fallback_tool_id": null,
        "notes": ""
      },
      "action": "run",
      "params": {},
      "working_directory": "."
    }
  ],
  "approval_required": true,
  "execution_notes": "approved plan",
  "feasibility": "full",
  "notes": "approved plan"
}
```

### `ai-config-dispatch` — マルチエージェント・ディスパッチ

Windows / PowerShell では `.venv\Scripts\ai-config-dispatch.cmd ...` を使う。

```bash
# タスクを分解・実行
ai-config-dispatch "バグを修正してテストを実行して"

# 計画のみ表示（実行しない）
ai-config-dispatch "新機能を実装して" --dry-run

# エージェント指定
ai-config-dispatch "コードレビュー" --agents gemini,codex

# 並列実行を有効化
ai-config-dispatch "テスト実行" --parallel

# ワークフロー利用
ai-config-dispatch "ログインバグ修正" --workflow bug-fix

# 利用可能なワークフロー一覧
ai-config-dispatch --list-workflows
```

| オプション | 説明 | デフォルト |
|---|---|---|
| `--agents` | 使用エージェント (カンマ区切り) | 自動検出 |
| `--cwd` | 作業ディレクトリ | `.` |
| `--max-retries` | ステップ毎の最大リトライ | `2` |
| `--max-replans` | 最大再計画回数 | `2` |
| `--dry-run` | 計画のみ表示 | off |
| `--parallel` | 並列実行の有効化 | off |
| `--workflow` | ワークフロー名 | なし |
| `--trace` | JSON トレース出力 | off |

### `ai-config-sources` — 外部ソース管理

```bash
ai-config-sources --repo-root . sync [--dry-run]
ai-config-sources --repo-root . list
ai-config-sources --repo-root . add <name> <url> --type mcp
ai-config-sources --repo-root . remove <name>
```

MCP source 管理と legacy manifest cleanup のみを担当します。skill 実ファイルの import / update / remove は扱いません。

### `ai-config-vendor-skills` — 外部 skill vendor layer

```bash
ai-config-vendor-skills --repo-root . sync-manifest [--prune] [--dry-run]
ai-config-vendor-skills --repo-root . import <source> [local-name] [--ref <commit-or-tag>]
ai-config-vendor-skills --repo-root . update --all
ai-config-vendor-skills --repo-root . remove <local-name>
ai-config-vendor-skills --repo-root . bootstrap-legacy --all
ai-config-vendor-skills --repo-root . cleanup-legacy-submodule <local-name>
ai-config-vendor-skills --repo-root . cleanup-legacy-submodule <local-name> --apply
```

通常運用の主経路は `sync-manifest` です。`bootstrap-legacy` と `cleanup-legacy-submodule` は migration utility であり、恒久運用の主経路ではありません。

---

## ワークフロー定義

よく使うタスクパターンを YAML で定義できます。

### 定義済みワークフロー

| ワークフロー | 説明 | ステップ |
|---|---|---|
| `bug-fix` | バグ修正 | 調査 → 修正 → テスト検証 |
| `code-review` | コードレビュー | 設計レビュー + セキュリティチェック + テスト検証（並列可） |
| `feature-build` | フィーチャー開発 | 設計 → 実装 → テスト |

### カスタムワークフロー作成

`workflows/` ディレクトリに YAML ファイルを作成します:

```yaml
name: my-workflow
description: "カスタムワークフローの説明"
variables:
  key: default_value
steps:
  - step_id: step-1
    description: "最初のステップ"
    agent: gemini           # gemini | codex | antigravity
    prompt_template: |
      {user_prompt} を分析してください。
    timeout_seconds: 300
  - step_id: step-2
    description: "次のステップ"
    agent: codex
    depends_on: [step-1]    # step-1 完了後に実行
    prompt_template: |
      分析結果に基づいて実装してください。
```

**テンプレート変数**:
- `{user_prompt}` — ユーザーの元のリクエスト
- カスタム変数は `variables` セクションで定義

---

## トラブルシューティング

### インデックス構築が失敗する

```
No records found. Check skills/, config/, and inventory/.
```

→ `skills/`、`config/master/ai-sync.yaml` が存在するか確認してください。

### MCP サーバーが起動しない

```
Index artifacts not found
```

→ `ai-config-index` でインデックスを先に構築してください。

### エージェントが見つからない

```
No CLI agents found. Install at least one of: gemini, codex, antigravity
```

→ `gemini`、`codex`、`antigravity` のいずれかの CLI がインストールされ、PATH に含まれていることを確認してください。

### ディスパッチのステップが繰り返し失敗する

1. `--dry-run` で計画を確認
2. `--trace` で詳細な実行ログを取得
3. エージェントの CLI が正しく動作するか個別に確認
