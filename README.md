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
- `mcp/weekly-report.bigquery_toolbox.prompt.md`: `bigquery_toolbox` 用の週次レポートプロンプトテンプレート
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
- `scripts/fetch-repos.ps1`: 依存リポジトリのclone/pull
- `scripts/setup-env-interactive.ps1`: `.env` を対話式で作成/更新
- `scripts/sync-open-webui-export.ps1`: Open WebUIエクスポートをAPI反映
- `scripts/export-antigravity.ps1`: Antigravityの設定・拡張マニフェストをエクスポート
- `scripts/import-antigravity.ps1`: Antigravityの設定・拡張マニフェストをインポート
- `scripts/restore-ai-workspace.ps1`: 新環境のゼロから復元（fetch -> env -> sync -> build -> test -> import）
- `scripts/run-ga4-last7d-sessions-cvr.ps1`: GA4「直近7日セッション/CVR」定型クエリ

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

# 依存リポジトリを取得/更新
./scripts/fetch-repos.ps1

# .env を対話式セットアップ
./scripts/setup-env-interactive.ps1

# Open WebUIエクスポートを反映（最新ファイル自動選択）
./scripts/sync-open-webui-export.ps1 -ExportDir <export-folder> -UseLatestFiles

# GA4: 直近7日セッション/CVRを取得
./scripts/run-ga4-last7d-sessions-cvr.ps1

# Antigravity設定をエクスポート（snapshot + latest）
./scripts/export-antigravity.ps1

# Antigravity設定をインポート
./scripts/import-antigravity.ps1

# 新環境の復元を一括実行
./scripts/restore-ai-workspace.ps1 -WorkspaceRoot $HOME -AiPlatformProfile core -ApplyOpenWebUiExport

# Open WebUI importの一部だけスキップしたい場合
./scripts/restore-ai-workspace.ps1 -WorkspaceRoot $HOME -ApplyOpenWebUiExport -SkipOpenWebUiConfig

# 復元時にAntigravity設定も同時インポート
./scripts/restore-ai-workspace.ps1 -WorkspaceRoot $HOME -ApplyAntigravityImport
```

## 新PCへの最短復元

`ai-config` だけ先にcloneできれば、以下の1コマンドで復元できます。

```powershell
cd $HOME/ai-config
pwsh ./scripts/restore-ai-workspace.ps1 -WorkspaceRoot $HOME -AiPlatformProfile core -ApplyOpenWebUiExport
```

- `core`: Open WebUI + mcp-router を優先して起動（GPU必須構成を回避）
- `full`: `-AiPlatformProfile full` で `ai-full` プロファイルを起動
- Antigravity設定も同時復元したい場合は `-ApplyAntigravityImport` を付与
- Open WebUIエクスポートを後で反映する場合は `sync-open-webui-export.ps1` を単体実行

## Antigravity の同期

```powershell
# 現在のAntigravity設定を ai-config に保存
pwsh ./scripts/export-antigravity.ps1

# 必要なら globalStorage も含める（機密情報が入りうるため通常は非推奨）
pwsh ./scripts/export-antigravity.ps1 -IncludeGlobalStorage

# 新環境で復元
pwsh ./scripts/import-antigravity.ps1
```

- エクスポート先は既定で `inventory/antigravity/` です
- `latest/` は復元用の最新スナップショット、`snapshot-YYYYMMDD-HHmmss/` は履歴です
- 拡張は `extensions-manifest.txt`（`publisher.name@version`）から再インストールします

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
