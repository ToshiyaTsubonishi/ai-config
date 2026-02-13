# ai-config

Codex / Gemini / Antigravity の `MCP` と `Skills` を1つのリポジトリで管理・同期するための設定リポジトリです。

## 方針

- MCPはテンプレート(`mcp/*.tmpl`)をGit管理し、`scripts/apply-mcp.ps1`で各ツールへ反映
- Skillsは`shared + agent-specific`のレイヤーで管理し、`scripts/sync-skills.ps1`で配布
- 現在のローカル状態は`scripts/export-inventory.ps1`で`inventory/*.json`へスナップショット
- `skills.sh`のランキング上位は`scripts/import-skills-sh-top.ps1`で取り込み
- 重複棚卸しは`scripts/audit-skill-duplicates.ps1`でレポート化

## ディレクトリ

- `mcp/codex.config.toml.tmpl`: Codex用MCPテンプレート
- `mcp/antigravity.mcp_config.json.tmpl`: Gemini/Antigravity用MCPテンプレート
- `skills/shared/`: 全ツール共通スキル
- `skills/codex/`: Codex専用スキル
- `skills/gemini/`: Gemini専用スキル
- `skills/antigravity/`: Antigravity専用スキル
- `skills/imported/skills-sh/`: skills.sh から導入したスキル保管領域
- `inventory/`: 検出済み skills / mcp の一覧JSON
- `scripts/apply-mcp.ps1`: MCPテンプレート反映
- `scripts/sync-skills.ps1`: レイヤー合成してスキル同期
- `scripts/export-inventory.ps1`: 現在状態のインベントリ出力
- `scripts/sync-all.ps1`: 一括実行
- `scripts/import-skills-sh-top.ps1`: skills.sh all-time上位を取り込み
- `scripts/audit-skill-duplicates.ps1`: 重複スキル棚卸し

## 初期セットアップ

1. `.env.example` を `.env` にコピー
2. 必要なAPIキーだけ `.env` に設定
3. 必要なら `skills/shared` / `skills/<agent>` にスキルを追加
4. 実行

```powershell
cd $HOME/ai-config
./scripts/sync-all.ps1
```

## 個別実行

```powershell
# MCPのみ反映（codex/gemini/antigravity）
./scripts/apply-mcp.ps1

# shared + agent-specific を合成して同期
# 優先順位: agent-specific > shared
# 既存の未管理スキルは保護。上書きしたい場合のみ -OverwriteExisting
./scripts/sync-skills.ps1 -OverwriteExisting

# 現在の状態を inventory/*.json に出力
./scripts/export-inventory.ps1

# skills.sh all-time上位500を導入（再実行でレジューム）
./scripts/import-skills-sh-top.ps1 -TopN 500

# 重複スキル棚卸しレポート生成
./scripts/audit-skill-duplicates.ps1
```

## Mac / Linuxで再現

PowerShell 7(`pwsh`) を使えば同じスクリプトで再現できます。

```bash
cd ~/ai-config
pwsh ./scripts/sync-all.ps1
```

- 反映先は `$HOME` 基準で解決されます
- 必要なら `.env` の `*_PATH` で上書きしてください
- `TopN 500` 取り込みはネットワークとディスクを使うため、初回は時間がかかります

## skills.sh 上位導入フロー

1. `./scripts/import-skills-sh-top.ps1 -TopN 500`  
2. `./scripts/audit-skill-duplicates.ps1`  
3. `inventory/skill-duplicates.md` を見て統合作業  
4. 採用するものだけ `skills/shared` または `skills/<agent>` に昇格  
5. `./scripts/sync-skills.ps1` で各ツールへ配布

現状メモ:
- `TopN 500` の取り込み実績は `498/500`（未解決: `stripe-best-practices`, `vue-development-guides`）
- 重複名は `19` 件（`inventory/skill-duplicates.md` に推薦keep先あり）

## 日々の追加運用

1. まず `skills/imported/skills-sh` に新規取り込み
2. `./scripts/audit-skill-duplicates.ps1` で重複確認
3. 採用候補を `skills/shared` または `skills/<agent>` に昇格
4. `./scripts/sync-skills.ps1` で配布
5. 定期的に `inventory/skill-duplicates.md` を見直し

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
