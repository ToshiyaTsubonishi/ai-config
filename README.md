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
  - `config/targets/antigravity/mcp_config.json.tmpl`
  - `config/targets/gemini-cli/settings.json.tmpl`
- コア同期スクリプト:
  - `scripts/sync/sync-mcp.ps1`
  - `scripts/sync/sync-skills.ps1`
- 互換ラッパー:
  - `scripts/apply-mcp.ps1`
  - `scripts/sync-skills.ps1`
  - `scripts/sync-all.ps1`

## 同期ロジック

### MCP

- 設定ソースは `ai-sync.yaml` の `targets.*.templates` と `path_profiles`
- `mcp_mode`
  - `replace`: テンプレートで完全置換
  - `merge`: JSON の `mcpServers` だけ既存設定へマージ（Gemini CLI 向け）

### Skills

- `skill_layers: ["shared", "target"]` の順で適用
- `skills_mode: "overlay"` の場合:
  - 同名ファイルは上書き
  - ターゲット側にしかないファイルは削除しない
- `skills_mode: "replace"` の場合:
  - ターゲット側をクリアしてから再配置

## 実行

```powershell
cd $HOME/ai-config
./scripts/sync-all.ps1
```

### 個別実行

```powershell
# MCPのみ
./scripts/sync/sync-mcp.ps1 -RepoRoot $HOME/ai-config

# Skillsのみ
./scripts/sync/sync-skills.ps1 -RepoRoot $HOME/ai-config

# DryRun
./scripts/sync/sync-mcp.ps1 -RepoRoot $HOME/ai-config -DryRun
./scripts/sync/sync-skills.ps1 -RepoRoot $HOME/ai-config -DryRun
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
- `GEMINI_CONFIG_PATH`
- `GEMINI_MCP_CONFIG_PATH`
- `ANTIGRAVITY_MCP_CONFIG_PATH`
- `CODEX_SKILLS_PATH`
- `GEMINI_SKILLS_PATH`
- `ANTIGRAVITY_SKILLS_PATH`

## その他スクリプト

- `scripts/sync-env-files.ps1`: 共有 `.env` の配布
- `scripts/export-inventory.ps1`: 現在状態のスナップショット出力
- `scripts/import-skills-sh-top.ps1`: skills.sh 上位の取り込み
- `scripts/audit-skill-duplicates.ps1`: スキル重複棚卸し
- `scripts/fetch-repos.ps1`: 依存リポジトリの clone/pull
- `scripts/restore-ai-workspace.ps1`: 新環境復元フロー

## 注意

- `.env` はコミットしないでください（`.gitignore` 対象）
- PowerShell 実行環境（`pwsh` 推奨）が必要です
- `sync-all.ps1 -DryRun` では環境同期と inventory 出力は実際には書き込みません
