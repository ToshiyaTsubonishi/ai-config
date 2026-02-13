# ai-config

Codex / Gemini / Antigravity の `MCP` と `Skills` を1つのリポジトリで管理・同期するための設定リポジトリです。

## 方針

- MCPはテンプレート(`mcp/*.tmpl`)をGit管理し、`scripts/apply-mcp.ps1`で各ツールへ反映
- Skillsは`skills/shared`を単一ソースにして、`scripts/sync-skills.ps1`で配布
- 現在のローカル状態は`scripts/export-inventory.ps1`で`inventory/*.json`へスナップショット

## ディレクトリ

- `mcp/codex.config.toml.tmpl`: Codex用MCPテンプレート
- `mcp/antigravity.mcp_config.json.tmpl`: Gemini/Antigravity用MCPテンプレート
- `skills/shared/`: 3ツールに同期する共通スキル
- `inventory/`: 検出済み skills / mcp の一覧JSON
- `scripts/apply-mcp.ps1`: MCPテンプレート反映
- `scripts/sync-skills.ps1`: 共通スキル同期
- `scripts/export-inventory.ps1`: 現在状態のインベントリ出力
- `scripts/sync-all.ps1`: 一括実行

## 初期セットアップ

1. `.env.example` を `.env` にコピー
2. 必要なAPIキーだけ `.env` に設定
3. 必要なら `skills/shared` に共通スキルを追加
4. 実行

```powershell
cd $HOME/ai-config
./scripts/sync-all.ps1
```

## 個別実行

```powershell
# MCPのみ反映（codex/gemini/antigravity）
./scripts/apply-mcp.ps1

# 既存の未管理スキルは保護。上書きしたい場合のみ -OverwriteExisting
./scripts/sync-skills.ps1 -OverwriteExisting

# 現在の状態を inventory/*.json に出力
./scripts/export-inventory.ps1
```

## 既定の反映先

- Codex MCP: `~/.codex/config.toml`
- Gemini MCP: `~/.gemini/antigravity/mcp_config.json`
- Antigravity MCP: `~/.antigravity/mcp_config.json`
- Codex Skills: `~/.codex/skills`
- Gemini Skills: `~/.gemini/skills`
- Antigravity Skills: `~/.gemini/antigravity/skills`

`.env` の `*_PATH` で上書き可能です。

## GitHub Private Repo化

```powershell
# 1) GitHub認証
# gh auth login

# 2) Private repo作成してpush
# gh repo create <repo-name> --private --source=. --remote=origin --push
```

## セキュリティ注意

- `.env` はコミットしないでください（`.gitignore` 済み）
- `inventory` にはキー値は保存せず、名前・件数のみを出力します
- もし既存設定にトークン直書きを見つけた場合は、環境変数化してトークンをローテーションしてください
