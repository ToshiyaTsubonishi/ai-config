# ai-config

Codex / Antigravity / Gemini CLI の `MCP` と `Skills` を一元管理して同期するリポジトリです。

## 対象ツール

- `codex`
- `antigravity`
- `gemini_cli`（Gemini Shell ではなく Gemini CLI）

デフォルト同期対象から Anthropic 系は外しています（`config/master/ai-sync.yaml` の `defaults.excluded_toolchains`）。

## 現在の構成

- マスター設定: `config/master/ai-sync.yaml`
- スキーマ: `schemas/ai-sync.schema.json`
- ターゲット別テンプレート:
  - `config/targets/codex/config.toml.tmpl`
  - `config/targets/codex/AGENTS.md.tmpl`
  - `config/targets/codex/AGENTS_RULES.md.tmpl`
  - `config/targets/antigravity/mcp_config.json.tmpl`
  - `config/targets/antigravity/GEMINI.md.tmpl`
  - `config/targets/antigravity/GEMINI_RULES.md.tmpl`
  - `config/targets/gemini-cli/settings.json.tmpl`
  - `config/targets/gemini-cli/GEMINI.md.tmpl`
  - `config/targets/gemini-cli/GEMINI_RULES.md.tmpl`
- コア同期スクリプト:
  - `scripts/sync/sync-mcp.ps1`
  - `scripts/sync/sync-skills.ps1`
  - `scripts/sync/sync-agent-context.ps1`
- 互換ラッパー:
  - `scripts/apply-mcp.ps1`
  - `scripts/sync-skills.ps1`
  - `scripts/sync/sync-gemini-context.ps1`（旧名互換）
  - `scripts/sync-all.ps1`

## 同期ロジック

### MCP

- 設定ソースは `ai-sync.yaml` の `targets.*.templates` と `path_profiles`
- `mcp_mode`
  - `replace`: テンプレートで完全置換
  - `merge`: JSON の `mcpServers` だけ既存設定へマージ（Gemini CLI 向け）

### Skills

- `skill_layers: ["shared", "target"]` の順で適用
- ベースラインは `https://github.com/tsytbns/antigravity-awesome-skills` の以下3系統を使用:
  - `skills/codex-cli` -> `skills/codex`
  - `skills/gemini-cli` -> `skills/gemini`
  - `skills/antigravity` -> `skills/antigravity`
- `skills_mode: "overlay"` の場合:
  - 同名ファイルは上書き
  - ターゲット側にしかないファイルは削除しない
- `skills_mode: "replace"` の場合:
  - ターゲット側をクリアしてから再配置

### Agent Context (`AGENTS.md` / `GEMINI.md` / Rules)

- `codex` / `gemini_cli` / `antigravity` で、ターゲットごとのコンテキストテンプレートをホーム配下へ同期
- デフォルト出力:
  - Codex: `${USERPROFILE}\.codex\AGENTS.md`, `${USERPROFILE}\.codex\AGENTS_RULES.md`
  - Gemini CLI: `${USERPROFILE}\.gemini\GEMINI.md`, `${USERPROFILE}\.gemini\GEMINI_RULES.md`
  - Antigravity: `${USERPROFILE}\.gemini\antigravity\GEMINI.md`, `${USERPROFILE}\.gemini\antigravity\GEMINI_RULES.md`
- 必要なら環境変数で出力先を上書き可能（後述）

### Dynamic Index Artifact 契約

`.index/summary.json` は検索側の実行契約として以下キーを必須扱いにします。

- `index_format_version`
- `embedding_backend`
- `vector_backend`
- `embedding_dim`

`index_format_version` は **3** を使用します。v1/v2 の index は互換移行せず、再構築が必要です。

## 実行

```powershell
cd $HOME/ai-config
./scripts/sync-all.ps1
```

`sync-all.ps1` はデフォルトで `scripts/import-antigravity-awesome-skills.ps1` を実行し、
`codex` / `gemini_cli` / `antigravity` 用のベースライン Skills を更新します。  
ベースライン取り込みをスキップする場合:

```powershell
./scripts/sync-all.ps1 -SkipBaselineSkillImport
```

### selector index 実行（分離準備）

`sync-all.ps1` は selector index 構築を `scripts/sync/run-selector-index.ps1` 経由で実行します。  
これにより、将来的に動的ツール選択ロジックを別リポジトリへ移行しても、`sync-all` 側は外部CLI呼び出しだけに保てます。

既定（ローカル fallback）:

```powershell
./scripts/sync-all.ps1
```

外部 selector CLI を明示:

```powershell
./scripts/sync-all.ps1 `
  -SelectorIndexCommand selector-cli `
  -SelectorIndexArgs @("build-index", "--repo-root", "{REPO_ROOT}")
```

index 構築をスキップ:

```powershell
./scripts/sync-all.ps1 -SkipSelectorIndex
```

### selector index watch モード

`skills/`, `config/`, `inventory/` の変更を監視し、debounce 後に再構築します。

```powershell
./scripts/sync/watch-selector-index.ps1 -RepoRoot $HOME/ai-config -DebounceSec 1.5
```

または Python CLI 直呼び出し:

```powershell
$env:PYTHONPATH="$HOME/ai-config/src"
.venv\Scripts\python.exe -m ai_config.build_index --repo-root $HOME/ai-config --watch --debounce-sec 1.5
```

### 動的検索 + 自己修復フロー

`ai-config-agent` は以下のグラフで処理します。

1. `retrieve_candidates`（Hybrid + RRF）
2. `plan_steps`（構造化 plan）
3. `execute_step`
4. `evaluate_step`
5. `repair_or_fallback`
6. 必要時のみ `re_retrieve`
7. `finalize`

最終応答には「採用ツール」「失敗と回復経路」「未達成事項」を含めます。

### agent CLI

```powershell
# 検索のみ
ai-config-agent "MCP設定を確認したい" --search-only --top-k 8

# フル実行（自己修復あり）
ai-config-agent "codex で実行して" --top-k 8 --max-retries 2 --trace
```

### 実行エンジンの未導入CLI挙動

`codex` / `gemini` / `antigravity` の CLI が未導入の場合、実行層は  
`EXECUTOR_NOT_AVAILABLE` を返し、Orchestrator は代替候補または再検索へフォールバックします。

### 個別実行

```powershell
# MCPのみ
./scripts/sync/sync-mcp.ps1 -RepoRoot $HOME/ai-config

# Skillsのみ
./scripts/sync/sync-skills.ps1 -RepoRoot $HOME/ai-config

# Agent context のみ (codex / gemini_cli / antigravity)
./scripts/sync/sync-agent-context.ps1 -RepoRoot $HOME/ai-config

# DryRun
./scripts/sync/sync-mcp.ps1 -RepoRoot $HOME/ai-config -DryRun
./scripts/sync/sync-skills.ps1 -RepoRoot $HOME/ai-config -DryRun
./scripts/sync/sync-agent-context.ps1 -RepoRoot $HOME/ai-config -DryRun
```

### 互換エイリアス

旧ターゲット名 `gemini` / `gemini_shell` / `gemini-cli` は自動的に `gemini_cli` へ変換されます。

## 既定パス（ai-sync.yaml）

- Codex
  - Windows: `${USERPROFILE}\.codex\config.toml`, `${USERPROFILE}\.codex\skills`
  - macOS: `${HOME}/.codex/config.toml`, `${HOME}/.codex/skills`
- Antigravity
  - Windows: `${USERPROFILE}\.gemini\antigravity\mcp_config.json`, `${USERPROFILE}\.gemini\antigravity\skills`
  - macOS: `${HOME}/.gemini/antigravity/mcp_config.json`, `${HOME}/.gemini/antigravity/skills`
- Gemini CLI
  - Windows: `${USERPROFILE}\.gemini\settings.json`, `${USERPROFILE}\.gemini\skills`
  - macOS: `${HOME}/.gemini/settings.json`, `${HOME}/.gemini/skills`

## 環境変数

`.env.example` を `.env` にコピーして必要値を設定してください。主な上書き変数:

- `CODEX_CONFIG_PATH`
- `CODEX_AGENTS_PATH`
- `CODEX_AGENTS_RULES_PATH`
- `GEMINI_CONFIG_PATH`
- `GEMINI_MCP_CONFIG_PATH`
- `ANTIGRAVITY_MCP_CONFIG_PATH`
- `GEMINI_SYSTEM_PROMPT_PATH`
- `GEMINI_RULES_PATH`
- `ANTIGRAVITY_SYSTEM_PROMPT_PATH`
- `ANTIGRAVITY_RULES_PATH`
- `CODEX_SKILLS_PATH`
- `GEMINI_SKILLS_PATH`
- `ANTIGRAVITY_SKILLS_PATH`

## その他スクリプト

- `scripts/sync-env-files.ps1`: 共有 `.env` の配布
- `scripts/export-inventory.ps1`: 現在状態のスナップショット出力
- `scripts/import-antigravity-awesome-skills.ps1`: `antigravity-awesome-skills` から `codex-cli` / `gemini-cli` / `antigravity` を取り込み
- `scripts/import-skills-sh-top.ps1`: 廃止（TopN 収集は基本設定から除外）
- `scripts/audit-skill-duplicates.ps1`: スキル重複棚卸し
- `scripts/fetch-repos.ps1`: 依存リポジトリの clone/pull
- `scripts/restore-ai-workspace.ps1`: 新環境復元フロー

## 注意

- `.env` はコミットしないでください（`.gitignore` 対象）
- PowerShell 実行環境（`pwsh` 推奨）が必要です
- `sync-all.ps1 -DryRun` では環境同期と inventory 出力は実際には書き込みません
- selector index 構築に失敗しても、`sync-all` は MCP/Skills/Context 同期を継続します（警告ログのみ）
