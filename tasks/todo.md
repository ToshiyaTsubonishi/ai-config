# TODO

## Plan
- [x] `instructions/` ディレクトリを作成し、`Agent.md` / `Gemini.md` / `Lesson.md` の保管場所を追加する
- [x] `Agent.md` 初版を `/Users/tsytbns/.codex/AGENTS.md` から作成し、`ai-config-selector` 参照と `ai-config-dispatch` 推奨ルールを追記する
- [x] ローカル保管ファイルと実運用ファイル（`~/.codex/AGENTS.md`, `~/.gemini/GEMINI.md`, `tasks/lessons.md`）を同期するスクリプトを追加する
- [x] README に運用手順を追記する
- [x] 同期スクリプトを検証し、レビュー結果を記録する

## Progress
- [x] 要件と既存構成を調査
- [x] 実装
- [x] 検証
- [x] レビュー記録

## Review
- 追加ファイル: `instructions/Agent.md`, `instructions/Gemini.md`, `instructions/Lesson.md`, `instructions/README.md`, `scripts/sync-instructions.sh`
- 更新ファイル: `README.md`
- 検証コマンド:
  - `bash scripts/sync-instructions.sh status`
  - `bash scripts/sync-instructions.sh pull --dry-run`
  - `bash scripts/sync-instructions.sh push --dry-run`
  - `bash scripts/sync-instructions.sh push`（実同期）
  - `bash scripts/sync-instructions.sh status`（最終確認）
- 検証結果: `agent/gemini/lesson` すべて `synced`

## 2026-03-09 Model Default Alignment

### Plan
- [x] Codex / Gemini / Claude 関連スキルのうち、特定モデルを既定値として案内している箇所を特定する
- [x] 実行時は各 CLI / サービスのローカル既定値を尊重する方針に文言をそろえる
- [x] 差分と検索結果を確認し、レビュー結果を記録する

### Progress
- [x] 調査
- [x] 実装
- [x] 検証
- [x] レビュー記録

### Review
- 更新ファイル:
  - `skills/imported/skills-sh/sources/softaworks__agent-toolkit/codex/SKILL.md`
  - `skills/imported/skills-sh/sources/softaworks__agent-toolkit/gemini/SKILL.md`
  - `tasks/todo.md`
- 検証コマンド:
  - `rg -n 'Uses GPT-5\\.2 by default|Uses Gemini 3 Pro by default|Default to \`gpt-5\\.2\`|recommended default|CLI defaults to \`gpt-5.2\`' skills/imported/skills-sh/sources/softaworks__agent-toolkit -S`
  - `.venv/bin/ai-config-index --repo-root . --profile default`
  - `python - <<'PY' ...` で `.index/records.json` の `skill:codex` / `skill:gemini` description を確認
- 検証結果:
  - `skill:codex` と `skill:gemini` の SKILL.md はローカル既定値尊重の文言に更新済み
  - `.index/records.json` 上の `skill:codex` / `skill:gemini` description も更新済み
  - 現在の `search_tools` 応答は MCP サーバーのキャッシュにより旧 description のままだが、サーバー再起動で追従する想定
  - `skill:claude` 相当の実行スキルで、同様に固定既定モデルを案内している index 対象は確認できなかった

## 2026-03-09 Managed MCP Propagation Trace

### Plan
- [x] `config/master/ai-sync.yaml` の managed MCP 定義と関連する生成経路のエントリポイントを特定する
- [x] user-facing config へ反映するスクリプト / 関数 / テンプレートを特定する
- [x] 新しい remote MCP server を env 認証付きで追加する最小変更ファイルと検証コマンドを確定する

### Progress
- [x] 調査
- [x] 伝播経路特定
- [x] 検証コマンド確認
- [x] レビュー記録

### Review
- 主要確認ファイル:
  - `config/master/ai-sync.yaml`
  - `src/ai_config/registry/mcp_parser.py`
  - `src/ai_config/registry/extractors.py`
  - `src/ai_config/build_index.py`
  - `src/ai_config/retriever/hybrid_search.py`
  - `scripts/register.sh`
- 結論:
  - `config/master/ai-sync.yaml` の `mcp_servers` は `scan_mcp_servers()` 経由で `.index/records.json` に取り込まれ、`ai-config-selector` の検索対象になる
  - 現在の user-facing config 書き込み経路は `scripts/register.sh` の `register_antigravity()` / `register_gemini_cli()` / `register_codex()` のみで、いずれも `ai-config-selector` だけを書き込む
  - `targets.*.path_profiles.*.mcp_file` は現状コード参照がなく、`config/master/ai-sync.yaml` から各ユーザー設定ファイルへ managed MCP を自動伝播する実装は存在しない
  - env 認証付き remote MCP を索引対象として追加する最小変更は `config/master/ai-sync.yaml` の `mcp_servers` に新規エントリを追加すること
  - その server を実際に Codex / Gemini / Antigravity の user-facing config に書き出したい場合は、`scripts/register.sh` に各ターゲット形式向けの出力ロジック追加が必要
- 検証コマンド:
  - `rg -n "path_profiles|mcp_file|enabled_targets|scan_mcp_servers|register_(antigravity|gemini_cli|codex)" src scripts config README.md docs`
  - `.venv/bin/ai-config-index --repo-root . --profile default`
  - `python3 - <<'PY'` で `.index/records.json` の `mcp:notion-mcp` / `mcp:google-knowledge-mcp` / `mcp:paper-search-mcp` の `source_path` と `env_keys` を確認
- 検証結果:
  - `.venv/bin/ai-config-index --repo-root . --profile default` は成功し、`ai_config.registry.mcp_parser: Parsed 12 MCP servers` を出力
  - `.index/records.json` 上で `config/master/ai-sync.yaml` 由来の managed MCP に `env_keys` が保持されていることを確認

## 2026-03-09 Raindrop MCP Registration

### Plan
- [x] Raindrop 公式 MCP 要件と既存の managed MCP パターンを確認する
- [x] `config/master/ai-sync.yaml` に Raindrop MCP を追加し、`.env` / `.env.example` に必要な変数を定義する
- [x] インデックスまたはテストで設定を検証し、レビュー結果を記録する

### Progress
- [x] 調査
- [x] 実装
- [x] 検証
- [x] レビュー記録

### Review
- 更新ファイル:
  - `config/master/ai-sync.yaml`
  - `.env`
  - `.env.example`
  - `src/ai_config/registry/mcp_parser.py`
  - `tasks/todo.md`
- 追加で更新した user-facing config:
  - `~/.codex/config.toml`
  - `~/.gemini/settings.json`
  - `~/.gemini/antigravity/mcp_config.json`
- 実装方針:
  - managed MCP では `bash -lc` + `mcp-remote` で Raindrop の hosted MCP (`https://api.raindrop.io/rest/v2/ai/mcp`) を登録
  - `RAINDROP_API_TOKEN` があれば `Authorization: Bearer ...` を付け、未設定時は公式 OAuth フローにフォールバック
  - クライアント設定側は公式ドキュメントどおり `npx -y mcp-remote https://api.raindrop.io/rest/v2/ai/mcp` を登録
  - ドキュメント上の Client ID / Client secret は今回の接続方式では不要なので `.env` には追加せず、実際に意味のある `RAINDROP_API_TOKEN` のみ定義
- 検証コマンド:
  - `.venv/bin/python - <<'PY' ... scan_mcp_servers(Path('.')) ... PY`
  - `.venv/bin/ai-config-index --repo-root . --profile default`
  - `python3 - <<'PY' ... .index/records.json から mcp:raindrop を確認 ... PY`
  - `sed -n '1,240p' ~/.codex/config.toml`
  - `sed -n '1,260p' ~/.gemini/settings.json`
  - `sed -n '1,220p' ~/.gemini/antigravity/mcp_config.json`
- 検証結果:
  - `scan_mcp_servers()` で `mcp:raindrop` の説明文と `env_keys=['RAINDROP_API_TOKEN']` を確認
  - `.venv/bin/ai-config-index --repo-root . --profile default` は成功し、`Parsed 13 MCP servers` を出力
  - `.index/records.json` に `mcp:raindrop` が登録され、説明文・`env_keys`・`source_path=config/master/ai-sync.yaml` が反映された
  - Codex / Gemini CLI / Antigravity の各設定ファイルに `raindrop` エントリが追記された

## 2026-03-09 Planning-First Orchestration

### Plan
- [ ] 現状の orchestrator / dispatch / registry / retriever / MCP の責務を保ったまま、承認可能な plan artifact の追加方針を確定する
- [ ] `orchestrator` に durable な plan schema / planner / validator / CLI plan-only 実行経路を追加する
- [ ] `dispatch` に approved structured plan 実行経路を追加し、既存 workflow / prompt planning と共存させる
- [ ] target / capability メタデータの揺れを最小限で正規化し、plan-time の選定根拠を安定化する
- [ ] テストと docs を更新し、差分を確認してコミットする

### Progress
- [x] 調査
- [x] 実装
- [x] 検証
- [x] レビュー記録

### Review
- 更新ファイル:
  - `src/ai_config/orchestrator/plan_schema.py`
  - `src/ai_config/orchestrator/planner.py`
  - `src/ai_config/orchestrator/validator.py`
  - `src/ai_config/orchestrator/cli.py`
  - `src/ai_config/dispatch/state.py`
  - `src/ai_config/dispatch/planner.py`
  - `src/ai_config/dispatch/dispatcher.py`
  - `src/ai_config/dispatch/evaluator.py`
  - `src/ai_config/registry/normalization.py`
  - `src/ai_config/registry/skill_parser.py`
  - `src/ai_config/registry/script_parser.py`
  - `src/ai_config/registry/extractors.py`
  - `src/ai_config/registry/mcp_parser.py`
  - `src/ai_config/retriever/query_intent.py`
  - `src/ai_config/retriever/hybrid_search.py`
  - `docs/architecture.md`
  - `docs/operations.md`
  - `docs/development.md`
  - `README.md`
  - `tests/test_orchestrator_plan_artifacts.py`
  - `tests/test_dispatch_approved_plan.py`
  - `tests/test_cli_smoke.py`
  - `tasks/todo.md`
- 実装要約:
  - `OrchestrationPlan` / `ToolReference` / `PlanValidationResult` を追加し、plan-only / execute-plan を CLI に追加
  - orchestrator planner を新設し、registry-backed candidate retrieval・validation・controlled replan metadata を実装
  - dispatch が approved structured plan を受け取り、tool execution を dependency order で実行できるよう拡張
  - target 正規化を導入し、`gemini` / `gemini_cli` などの揺れを retriever / parser 側で吸収
- 検証コマンド:
  - `.venv/bin/python -m pytest tests/test_orchestrator_plan_artifacts.py tests/test_dispatch_approved_plan.py tests/test_cli_smoke.py tests/test_dispatch_planner.py tests/test_dispatch_graph.py tests/test_dispatch_workflow.py tests/test_dispatch_fixes.py tests/test_orchestrator_router.py tests/test_orchestrator_repair_loop.py tests/test_mcp_server_tools.py tests/test_retriever_rrf.py -q`
  - `.venv/bin/python -m pytest tests/ -q`
- 検証結果:
  - 部分回帰テストは `70 passed`
  - 全テストは `91 passed, 2 skipped`

## 2026-03-09 Raindrop Selector-Only Registration

### Plan
- [x] `ai-config-selector` 上で `mcp:raindrop` が検索可能であることを確認する
- [x] Codex / Gemini CLI / Antigravity の user-facing config から直接登録された `raindrop` MCP を削除する
- [x] repo 内の managed catalog 定義は維持しつつ、レビュー結果を記録する

### Progress
- [x] 要件確認
- [x] 実装
- [x] 検証
- [x] レビュー記録

### Review
- repo 内の catalog 定義は `config/master/ai-sync.yaml` の `mcp_servers.raindrop` を維持し、`ai-config-selector` の検索対象として残した
- user-facing config からは `raindrop` を削除した
  - `~/.codex/config.toml`
  - `~/.gemini/settings.json`
  - `~/.gemini/antigravity/mcp_config.json`
- 検証結果:
  - `search_tools("raindrop bookmark mcp")` で `mcp:raindrop` が引き続き返ることを確認
  - Codex / Gemini CLI / Antigravity の各設定ファイルで `mcpServers.ai-config-selector` のみ残り、`raindrop` の直接登録が消えていることを確認
