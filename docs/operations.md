# ai-config 運用ガイド

## セットアップ

### 前提条件

- **Python 3.11 以上**
- **Git**（外部ソース管理に必要）
- AI ツール（Claude Code / Codex / Antigravity / Gemini CLI）のいずれか

### 初回セットアップ

```bash
git clone https://github.com/ToshiyaTsubonishi/ai-config.git
cd ai-config
bash scripts/setup.sh
```

`scripts/setup.sh` は以下を行います:
1. Python 仮想環境（`.venv`）の作成
2. 依存パッケージのインストール
3. `.env.example` を `.env` にコピー（初回のみ）

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

```bash
# 全ツールに一括登録
bash scripts/register.sh

# 個別登録
bash scripts/register.sh claude
bash scripts/register.sh antigravity
bash scripts/register.sh gemini_cli
bash scripts/register.sh codex
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

### 外部ソースの管理

```bash
# ソース一覧の確認
ai-config-sources --repo-root . list

# 全ソースの同期（追加・更新・削除）
ai-config-sources --repo-root . sync

# 事前確認（変更は行わない）
ai-config-sources --repo-root . sync --dry-run

# 新しいソースの追加
ai-config-sources --repo-root . add my-skills https://github.com/user/skills.git

# ソースの削除
ai-config-sources --repo-root . remove my-skills
```

### 推奨ワークフロー（ソース更新後）

```bash
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
ai-config-sources --repo-root . add <name> <url>
ai-config-sources --repo-root . remove <name>
```

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
