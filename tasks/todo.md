# TODO

## 2026-03-24 Selector Platform Boundary Refactor

### Plan
- [ ] 現状の selector / planner / execution / dispatch の責務と依存を棚卸しし、差分を architecture docs に反映する
- [ ] approved plan の stable contract を中立モジュールに切り出し、schema version / validation / subprocess boundary を定義する
- [ ] orchestrator CLI を `search` / `plan` / `execute-approved-plan` 中心に再設計し、dispatch 直接 import をなくす
- [ ] dispatch 側を approved plan execution runtime として接続し、ai-config からは execute abstraction 経由で呼ぶ
- [ ] README / architecture / operations / development / overview / constitution を新方針に合わせて更新する
- [ ] 関連テストと CLI smoke を更新し、移行上の残課題を review に記録する

### Progress
- [x] 現状調査
- [x] contract 設計
- [x] test 追加
- [x] code 実装
- [x] docs 更新
- [x] 検証
- [x] review

### Review
- 更新ファイル:
  - `src/ai_config/contracts/approved_plan.py`
  - `src/ai_config/executor/plan_boundary.py`
  - `src/ai_config/orchestrator/cli.py`
  - `src/ai_config/orchestrator/planner.py`
  - `src/ai_config/orchestrator/plan_schema.py`
  - `src/ai_config/orchestrator/validator.py`
  - `src/ai_config/dispatch/cli.py`
  - `src/ai_config/dispatch/planner.py`
  - `src/ai_config/mcp_server/runtime.py`
  - `README.md`
  - `docs/architecture.md`
  - `docs/operations.md`
  - `docs/development.md`
  - `docs/overview.md`
  - `docs/constitution.md`
  - `tests/test_approved_plan_contract.py`
  - `tests/test_plan_boundary.py`
  - `tests/test_cli_smoke.py`
  - `tests/test_selector_serving.py`
- 実装要約:
  - approved plan と execution request を `contracts/` に切り出し、`kind` / `schema_version` / validation rule を中立 contract として定義した
  - `orchestrator/cli.py` から `dispatch` 直接 import を削除し、`DispatchCLIPlanExecutor` の subprocess boundary に置き換えた
  - `ai-config-agent` は `search` / `plan` / `execute-approved-plan` / `schema` を標準 surface にし、legacy flag を互換経路として残した
  - `dispatch/` から `orchestrator/` への直接依存をなくし、contract module を介して approved plan を受ける runtime に寄せた
  - `selector-serving` readiness payload に `surface` / `runtime_mode` / `required_artifacts` を追加し、標準 deploy surface の意味をコードでも明示した
  - docs を selector platform / planner artifact / dispatch runtime boundary 前提へ更新した
- 移行メモ:
  - 現時点の dispatch は repo 内 compatibility runtime のまま残している
  - `AI_CONFIG_DISPATCH_CMD` を使えば、将来 external dispatch runtime へ切り替えても planner 側の public surface を維持できる
  - 次段では `dispatch` 側 request/response schema を repo 外へ持ち出す packaging と workflow asset の移送を行う
- 検証コマンド:
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_approved_plan_contract.py tests/test_plan_boundary.py tests/test_cli_smoke.py tests/test_dispatch_approved_plan.py tests/test_dispatch_graph.py tests/test_dispatch_planner.py tests/test_dispatch_workflow.py tests/test_dispatch_fixes.py tests/test_orchestrator_plan_artifacts.py tests/test_orchestrator_router.py tests/test_orchestrator_toolchain_bias.py tests/test_selector_serving.py tests/test_mcp_server_extended.py tests/test_mcp_server_tools.py tests/test_index_builder_contract.py -q`
  - `PYTHONPATH=src .venv/bin/python -m ai_config.orchestrator.cli --help`
  - `PYTHONPATH=src .venv/bin/python -m ai_config.orchestrator.cli schema approved-plan-execution-request`
  - `PYTHONPATH=src .venv/bin/python -m ai_config.dispatch.cli --help`
  - `git diff --check`
- 検証結果:
  - 主要回帰テスト 80 件が成功した
  - `ai-config-agent --help` は subcommand based surface を表示し、`schema` から contract JSON schema を確認できた
  - `ai-config-dispatch --help` は `--execute-approved-plan` と `--json` を公開した
  - `git diff --check` は clean だった

## 2026-03-24 macOS Selector Registration Repair

### Plan
- [x] 現状の user-home 設定と repo 内セットアップ手順を確認し、未設定原因を特定する
- [x] `scripts/register.sh` を使って macOS 向けの `ai-config-selector` 登録を修復する
- [x] `search_tools` 到達性と主要設定ファイルの反映を確認する
- [x] レビュー結果を `tasks/todo.md` に記録する

### Progress
- [x] 現状確認
- [x] register 実行
- [x] 動作確認
- [x] review

### Review
- 原因:
  - `~/.codex/config.toml` と `~/.gemini/settings.json`、`~/.gemini/antigravity/mcp_config.json` が `C:\Users\tsytbns\GitHub\ai-config\...` の旧 Windows パスを指していた
  - macOS では shell PATH 上に `ai-config-selector` という別名 CLI は不要で、各 AI ツールが `ai-config-selector` という MCP 名で `ai-config-mcp-server` を起動する構成が正
- 実行:
  - `cp ~/.codex/config.toml ~/.codex/config.toml.20260324-selector-fix.bak`
  - `cp ~/.gemini/settings.json ~/.gemini/settings.json.20260324-selector-fix.bak`
  - `cp ~/.gemini/antigravity/mcp_config.json ~/.gemini/antigravity/mcp_config.json.20260324-selector-fix.bak`
  - `cp ~/.claude.json ~/.claude.json.20260324-selector-fix.bak`
  - `bash scripts/register.sh all`
- 検証:
  - `~/.codex/config.toml`
  - `~/.gemini/settings.json`
  - `~/.gemini/antigravity/mcp_config.json`
  - `~/.claude.json`
  - `PYTHONPATH=src .venv/bin/python - <<'PY' ... ClientSession ... search_tools/get_tool_detail ... PY`
- 検証結果:
  - 4 つの user-home 設定ファイルはすべて `/Users/tsytbns/Documents/GitHub/ai-config/.venv/bin/ai-config-mcp-server --repo-root /Users/tsytbns/Documents/GitHub/ai-config` を参照する状態になった
  - ローカル selector MCP の `list_tools` / `search_tools` / `get_tool_detail` が成功し、base tools 7 個の公開と検索応答を確認した

## 2026-03-19 Cloud Run Selector Serving

### Plan
- [x] MCP server factory を整理し、selector read tools と extended execution tools を分離する
- [x] `streamable-http` transport と HTTP bind options を既存 `ai-config-mcp-server` に追加する
- [x] strict runtime index validator と Cloud Run 用 `ai-config-selector-serving` entrypoint を追加する
- [x] selector-serving の health/readiness endpoint と fail-fast behavior を追加する
- [x] Cloud Run Dockerfile / deploy docs / repo docs を更新する
- [x] selector-serving と既存 MCP server の HTTP/stdio 回帰テストを追加し、関連テストを実行する

### Progress
- [x] server refactor
- [x] runtime validator
- [x] selector-serving entrypoint
- [x] tests
- [x] Docker / deploy docs
- [x] verification
- [x] review

### Review
- 更新ファイル:
  - `pyproject.toml`
  - `src/ai_config/mcp_server/server.py`
  - `src/ai_config/mcp_server/runtime.py`
  - `src/ai_config/mcp_server/serving.py`
  - `tests/test_mcp_server_extended.py`
  - `tests/test_selector_serving.py`
  - `deploy/cloudrun/Dockerfile`
  - `deploy/cloudrun/README.md`
  - `README.md`
  - `docs/architecture.md`
  - `docs/operations.md`
  - `docs/development.md`
  - `tasks/todo.md`
- 実装要約:
  - `create_server()` を shared factory 化し、selector read tools と extended execution/downstream MCP tools を分離した
  - `ai-config-mcp-server` は `stdio` default を維持したまま `streamable-http` / host / port / path / stateless mode を受けられるようにした
  - `validate_runtime_index()` を追加し、`.index` の required artifacts と `HybridRetriever` 初期化を startup で検証するようにした
  - `ai-config-selector-serving` を追加し、Cloud Run では selector read API だけを `streamable-http` + `stateless_http=True` で公開し、`/healthz` と `/readyz` を追加した
  - Dockerfile は image build 中に `sync-manifest` と `ai-config-index` を実行し、runtime は `skills/` / `config/` / `.index/` を read-only に使うだけの構成にした
- 検証コマンド:
  - `.venv/bin/python -m pytest tests/test_mcp_server_extended.py tests/test_selector_serving.py -q`
  - `.venv/bin/python -m pytest tests/test_mcp_server_tools.py -q`
  - `.venv/bin/python -m pytest tests/test_mcp_server_extended.py tests/test_selector_serving.py tests/test_mcp_server_tools.py tests/test_cli_smoke.py tests/test_index_builder_contract.py -q`
  - `git diff --check`
  - `.venv/bin/python -m pip install . --quiet`
  - `.venv/bin/ai-config-selector-serving --help`
  - `.venv/bin/ai-config-mcp-server --help`
- 検証結果:
  - selector-serving / MCP HTTP regression / CLI smoke / index contract を含む関連テスト 16 件が成功した
  - `git diff --check` は clean だった
  - `ai-config-selector-serving` と拡張後の `ai-config-mcp-server` の help 表示が正常に出た
  - Docker image build 自体は network 依存の vendor materialization を含むため、このセッションでは未実行

## 2026-03-12 Phase 4 Core Retrieval Quality

### Plan
- [ ] `implementation_plan.md` の残タスクを current architecture に再マップし、obsolete な vendor migration 項目と live な core 強化項目を切り分ける
- [ ] default profile を前提にした retrieval evaluation corpus を追加し、代表クエリごとの期待 tool / skill を固定する
- [ ] retriever の品質を測る指標と実行経路を追加する（少なくとも recall@k / MRR / sentinel query regression）
- [ ] `HybridRetriever` の ranking 改善を行う（RRF weight / exact-match boost / intent-aware bias の順で小さく検証する）
- [ ] `profile_loader` や planner に入れるべき改善は retrieval 評価の結果を見て次段に切り出す
- [ ] docs / tests / benchmark 結果を残し、Phase 4 の次タスクを planner quality か profile policy かで再判定する

### Progress
- [x] `implementation_plan.md` の確認
- [x] current repo 状態との比較
- [ ] eval corpus
- [ ] evaluation harness
- [ ] retriever tuning
- [ ] docs
- [ ] review

### Review
- 判定:
  - `implementation_plan.md` の vendor migration / source manager cleanup / legacy cleanup / observability は現 repo で概ね完了している
  - 元計画のうち live な残項目は `retriever` 品質改善、`profile_loader` ポリシー拡張、`orchestrator` plan 品質向上
  - 着手順は `retriever` → `profile_loader` / planner の順が妥当。candidate quality が安定していない状態で planner をいじると因果が見えにくくなるため
- 次作業の推奨:
  - まず selector / orchestrator / dispatch の共通入口である `HybridRetriever` の測定基盤と品質改善を優先する
  - いきなり reranker を足すのではなく、評価 corpus と baseline を先に置き、RRF / lexical / exact-match の改善余地を確認してから追加の rerank 要否を判定する

## 2026-03-12 Vendor-Aware Observability

### Plan
- [x] vendor layer の shared inspection API を追加し、`status` と `doctor` で再利用する
- [x] `ai-config-vendor-skills status` を追加し、local-only / non-destructive / network-free な vendor state 観測を実装する
- [x] `status --json` に stable schema を持たせ、`schema_version` と `generated_at` を含める
- [x] `ai-config-doctor` に vendor manifest / materialization / git hygiene / index presence / extra local / unmanaged local checks を追加する
- [x] docs / tests / CLI 実行確認 / diff hygiene を完了し、レビューを記録する

### Progress
- [x] 調査
- [x] inspection layer
- [x] vendor status CLI
- [x] doctor 拡張
- [x] docs
- [x] 検証
- [x] レビュー記録

### Review
- 更新ファイル:
  - `src/ai_config/vendor/models.py`
  - `src/ai_config/vendor/skill_vendor.py`
  - `src/ai_config/vendor/cli.py`
  - `src/ai_config/doctor.py`
  - `tests/test_vendor_skills.py`
  - `tests/test_doctor.py`
  - `README.md`
  - `docs/operations.md`
  - `tasks/todo.md`
  - `tasks/lessons.md`
- 実装要約:
  - vendor layer に `inspect_vendor_state()` を追加し、manifest entry と local external dir を read-only に分類する shared inspection layer を作成した
  - `ai-config-vendor-skills status` を追加し、human output と `schema_version` / `generated_at` 付き JSON 出力を提供した
  - `ai-config-doctor` に vendor-aware checks を追加し、`extra_local` は pass with details、`unmanaged_local` は fail として扱うようにした
  - `tasks/lessons.md` に observability API では severity と JSON contract を先に固定するルールを追記した
- 検証コマンド:
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_vendor_skills.py tests/test_doctor.py tests/test_source_manager.py tests/test_cli_smoke.py tests/test_registry_external_mcp_catalog_parser.py tests/test_retriever_rrf.py -q`
  - `PYTHONPATH=src .venv/bin/python -m ai_config.vendor.cli --repo-root . status`
  - `PYTHONPATH=src .venv/bin/python -m ai_config.vendor.cli --repo-root . status --json`
  - `PYTHONPATH=src .venv/bin/python - <<'PY' ... _vendor_observability_checks(Path('.').resolve()) ... PY`
  - `PYTHONPATH=src .venv/bin/python -m ai_config.doctor --repo-root . --json`
  - `git diff --check`
- 検証結果:
  - 関連回帰テスト 29 件がすべて成功した
  - 実 repo の `ai-config-vendor-skills status` は 7 manifest entry すべて `ready`、`extra_local=0`、`unmanaged_local=0` を返した
  - `status --json` は `schema_version=1`、UTC `generated_at`、stable summary / entries 構造を返した
  - vendor-only doctor helper では `vendor_manifest` / `vendor_materialization` / `vendor_git_hygiene` / `vendor_index_presence` / `vendor_extra_local` / `vendor_unmanaged_local` がすべて pass だった
  - full `ai-config-doctor --json` も vendor checks 自体は pass だったが、既存の instruction drift と `antigravity` CLI 未導入により全体 exit code は 1 になった
  - `git diff --check` は clean だった

## 2026-03-12 Phase 2 Legacy Cleanup

### Plan
- [x] `config/vendor_skills.yaml` と vendor manifest loader を追加し、skill source seed を branch+ref pin で管理する
- [x] vendor CLI に `sync-manifest` と `cleanup-legacy-submodule` を追加し、no-prune default / safe cleanup 手順を実装する
- [x] setup を vendor manifest materialization → index build に更新し、`--skip-vendor-sync` / `-SkipVendorSync` を追加する
- [x] `.gitignore` / `.gitmodules` / `config/sources.yaml` を Phase 2 の MCP-only + vendor-managed artifact 方針に移行する
- [x] staged cleanup を `remotion` 単体 dry-run/apply → all dry-run/apply の順で実施し、selector/index/git 状態を確認する
- [x] docs / tests / review を更新し、Phase 2 完了条件を検証する

### Progress
- [x] 調査
- [x] vendor manifest
- [x] sync-manifest
- [x] cleanup utility
- [x] setup
- [x] metadata transition
- [x] staged cleanup
- [x] docs
- [x] 検証
- [x] レビュー記録

### Review
- 更新ファイル:
  - `src/ai_config/vendor/models.py`
  - `src/ai_config/vendor/skill_vendor.py`
  - `src/ai_config/vendor/cli.py`
  - `src/ai_config/source_manager.py`
  - `config/vendor_skills.yaml`
  - `config/sources.yaml`
  - `.gitignore`
  - `skills/external/.gitkeep`
  - `scripts/setup.sh`
  - `scripts/setup.ps1`
  - `tests/test_vendor_skills.py`
  - `README.md`
  - `docs/overview.md`
  - `docs/architecture.md`
  - `docs/operations.md`
  - `docs/development.md`
  - `tasks/todo.md`
- 実装要約:
  - `config/vendor_skills.yaml` を追加し、curated external skill source を exact `ref` で pin する Phase 2 manifest を導入した
  - vendor layer に `requested_ref`、manifest loader、`sync-manifest`、`cleanup-legacy-submodule` を追加し、default no-prune / preview-first cleanup を実装した
  - setup は vendor manifest materialization → default index build に更新し、`--skip-vendor-sync` / `-SkipVendorSync` を追加した
  - `config/sources.yaml` は MCP-only に移行し、`.gitignore` と `skills/external/.gitkeep` で external payload を vendor-managed local artifact として扱う形にした
  - actual repo で `remotion` 単体 cleanup 後に `--all` cleanup を実行し、legacy skill submodule をすべて local artifact に変換した
- 検証コマンド:
  - `.venv/bin/python -m pytest tests/test_vendor_skills.py -q`
  - `.venv/bin/python -m pytest tests/test_vendor_skills.py tests/test_source_manager.py tests/test_cli_smoke.py tests/test_registry_external_mcp_catalog_parser.py tests/test_retriever_rrf.py -q`
  - `.venv/bin/ai-config-vendor-skills --repo-root . cleanup-legacy-submodule remotion`
  - `.venv/bin/ai-config-vendor-skills --repo-root . cleanup-legacy-submodule remotion --apply`
  - `.venv/bin/ai-config-vendor-skills --repo-root . cleanup-legacy-submodule --all`
  - `.venv/bin/ai-config-vendor-skills --repo-root . cleanup-legacy-submodule --all --apply`
  - `.venv/bin/ai-config-vendor-skills --repo-root . sync-manifest`
  - `bash scripts/setup.sh`
  - `.venv/bin/ai-config-sources --repo-root . list`
  - `.venv/bin/ai-config-sources --repo-root . sync --dry-run`
  - `git submodule status`
  - `git diff --check`
- 検証結果:
  - vendor tests 10 件、関連回帰テスト合計 23 件が成功した
  - `cleanup-legacy-submodule` は single-repo dry-run/apply → all dry-run/apply の順で成功し、2 回目以降は `already_clean` で安全にスキップできる
  - `sync-manifest` は cleanup 後の local payload を exact ref に対して network なしで `aligned` / `up_to_date` 判定できた
  - `bash scripts/setup.sh` は vendor sync `up_to_date` → default profile index build を完走し、`total_records=1514` の index を再構築した
  - `.index` に対する `HybridRetriever` / `ToolIndex` の `streamlit app skill` 検索が通り、external streamlit skill が返った
  - `ai-config-sources list` は `No sources declared.`、`sync --dry-run` は空変更で、`config/sources.yaml` が MCP-only になっていることを確認した
  - `git submodule status` は空になり、`.gitmodules` は削除された
  - `git status --short --ignored skills/external` では external payload が `!!` で無視され、legacy submodule 内 `.import.json` による untracked noise は解消された
  - `git diff --check` は clean だった

## 2026-03-12 Phase 1 Vendor Layer

### Plan
- [x] repo 内 vendor CLI / vendor library を追加し、skill import/update/remove/provenance の canonical 実装を作る
- [x] `bootstrap-legacy` migration utility を追加し、既存 `skills/external/*` の provenance backfill 経路を作る
- [x] provenance 確立を前提にした minimal E2E tests を追加し、index / retrieval の継続性を確認する
- [x] `scripts/import-skill.sh` を vendor CLI 互換 wrapper に置き換える
- [x] `ai-config-sources` を MCP-only + legacy config cleanup に縮退し、skill 実ファイル責務を外す
- [x] docs を vendor layer / selector-first / migration utility 前提に更新する
- [x] 対象テストと CLI 検証を実行し、レビューを記録する

### Progress
- [x] 調査
- [x] vendor library
- [x] provenance bootstrap
- [x] minimal E2E
- [x] wrapper
- [x] source_manager 縮退
- [x] docs
- [x] 検証
- [x] レビュー記録

### Review
- 更新ファイル:
  - `src/ai_config/vendor/__init__.py`
  - `src/ai_config/vendor/models.py`
  - `src/ai_config/vendor/skill_vendor.py`
  - `src/ai_config/vendor/cli.py`
  - `src/ai_config/source_manager.py`
  - `scripts/import-skill.sh`
  - `pyproject.toml`
  - `scripts/setup.ps1`
  - `tests/test_vendor_skills.py`
  - `tests/test_source_manager.py`
  - `README.md`
  - `docs/overview.md`
  - `docs/architecture.md`
  - `docs/operations.md`
  - `docs/development.md`
  - `config/sources.yaml`
  - `tasks/todo.md`
- 実装要約:
  - `ai-config-vendor-skills` を追加し、repo 内 vendor CLI で import / update / remove / provenance を管理する形に移した
  - `bootstrap-legacy` を migration utility として追加し、既存 `skills/external/*` と `.gitmodules` から `.import.json` を backfill できるようにした
  - `scripts/import-skill.sh` は薄い互換 wrapper に置き換え、実ロジックを Python 側へ一本化した
  - `ai-config-sources` は MCP-only + legacy config cleanup に縮退し、skill 実ファイルの削除責務を外した
  - docs を vendor layer / selector-first / migration utility 前提に更新した
- 検証コマンド:
  - `.venv/bin/python -m pytest tests/test_vendor_skills.py -q`
  - `.venv/bin/python -m pytest tests/test_vendor_skills.py tests/test_source_manager.py -q`
  - `.venv/bin/python -m pytest tests/test_vendor_skills.py tests/test_source_manager.py tests/test_cli_smoke.py tests/test_registry_external_mcp_catalog_parser.py tests/test_retriever_rrf.py -q`
  - `scripts/import-skill.sh <temp-local-git-repo> wrapper-demo --dry-run`
- 検証結果:
  - vendor layer の import / force re-import / orphan cleanup / bootstrap legacy / CLI bootstrap-update-index-search が通った
  - `source_manager` の delegated skill listing、MCP-only sync、skill add reject、manifest-only remove が通った
  - wrapper は `.venv` 再インストールなしでも `PYTHONPATH=src` 付きで新しい vendor CLI を呼び出せることを確認した
  - 関連回帰テスト 17 件がすべて成功した
  - 追加の運用確認として `HEAD=91797b6` の clean working tree から `ai-config-vendor-skills --repo-root . bootstrap-legacy --all --dry-run` と `bootstrap-legacy --all` を実行し、7 つの legacy external checkout に `.import.json` が生成されることを確認した
  - その後 `ai-config-index --repo-root . --profile default` が成功し、`total_records=1508`、`skills=820`、`external_mcp_catalog=154` を含む index rebuild が通った
  - `.index` を使った `HybridRetriever` / `ToolIndex` の検索と local MCP selector の `search_tools('streamlit app skill')` が通り、external streamlit skill が検索結果に出ることを確認した
  - `git diff --check` は clean だった
  - 既存 external repo がまだ submodule なので、生成された `.import.json` は各 submodule 内の untracked file として見えている。これは Phase 1 の動作確認としては許容し、Phase 2 legacy cleanup の入力として扱う

## 2026-03-11 Editor Restart Runtime Validation

### Plan
- [x] 再起動後の Codex 設定と MCP 登録状態を確認する
- [x] `ai-config-selector` の到達性と基本ツール呼び出しを確認する
- [x] `ai-config-dispatch` の実行経路を確認する
- [x] 検証結果をレビューに記録する

### Progress
- [x] 調査
- [x] 設定確認
- [x] selector 検証
- [x] dispatch 検証
- [x] レビュー記録

### Review
- 確認項目:
  - `~/.codex/config.toml` に `mcp_servers.ai-config-selector` が残っており、command は `/Users/tsytbns/Documents/GitHub/ai-config/.venv/bin/ai-config-mcp-server` を指している
  - `.venv/bin/ai-config-mcp-server` と `.venv/bin/ai-config-dispatch` は実行可能のまま存在する
- selector 検証:
  - 現セッションで `search_tools` / `get_tool_detail` / `get_tool_count` / `list_categories` が成功した
  - `get_tool_count` は `1298`、カテゴリ集計も正常に返った
  - downstream MCP として `mcp:microsoft-learn-mcp` に対し `list_mcp_server_tools(refresh=true)` が成功し、3 tools を取得した
  - 同 MCP に対し `call_mcp_server_tool("microsoft_docs_search", {"query":"Azure OpenAI quickstart"})` が成功した
- dispatch 検証:
  - `AI_CONFIG_GEMINI_CMD=echo AI_CONFIG_CODEX_CMD=echo .venv/bin/ai-config-dispatch "editor restart runtime validation" --workflow code-review --parallel` が成功した
  - `design-review` / `security-review` / `test-review` の 3 step 並列 dispatch が完走した

## 2026-03-11 Re-Setup And Selector/Dispatch Validation

### Plan
- [x] 現行の `.venv` / CLI ランナー / 依存状態を確認する
- [x] `scripts/setup.sh` を再実行して環境を再セットアップする
- [x] `ai-config-selector` の検索・詳細取得が意図通り機能することを確認する
- [x] `ai-config-dispatch` の CLI 実行経路を確認し、意図したオーケストレーションが走ることを検証する
- [x] 検証結果と残課題をレビューに記録する

### Progress
- [x] 調査
- [x] 再セットアップ
- [x] selector 検証
- [x] dispatch 検証
- [x] レビュー記録

### Review
- 実行コマンド:
  - `bash scripts/setup.sh`
  - `PYTHONPATH=src .venv/bin/python - <<'PY' ... local selector MCP call ... PY`
  - `.venv/bin/python -m pytest tests/test_mcp_server_tools.py tests/test_mcp_server_extended.py tests/test_cli_smoke.py tests/test_dispatch_approved_plan.py tests/test_dispatch_graph.py tests/test_dispatch_planner.py tests/test_dispatch_workflow.py tests/test_dispatch_fixes.py -q`
  - `AI_CONFIG_GEMINI_CMD=echo AI_CONFIG_CODEX_CMD=echo .venv/bin/ai-config-dispatch "selector/dispatch setup validation" --workflow bug-fix --trace --keep-context`
  - `AI_CONFIG_GEMINI_CMD=echo AI_CONFIG_CODEX_CMD=echo .venv/bin/ai-config-dispatch "selector/dispatch setup validation" --workflow code-review --parallel --trace`
- 検証結果:
  - `scripts/setup.sh` は依存再インストールと `.index` 再構築まで成功し、`total_records=1298` を出力した
  - ローカル `ai-config-selector` MCP server に対する `search_tools` / `get_tool_detail` / `get_tool_count` / `list_categories` 呼び出しが成功した
  - `tests/test_mcp_server_extended.py` を含む対象テスト 63 件がすべて成功し、selector の downstream MCP `list_mcp_server_tools` / `call_mcp_server_tool` 経路も通過した
  - `ai-config-dispatch` は `bug-fix` workflow で依存付き順次実行と `.dispatch/<session>` への context handoff を確認した
  - `ai-config-dispatch` は `code-review` workflow で 3 step の並列 dispatch を確認した
- 残留生成物:
  - `--keep-context` 検証により `.dispatch/9a7aeb7d/` が残っている

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

## 2026-03-09 Local Environment Setup Cleanup

### Plan
- [x] 現行の user-facing config 対象を確認する（Claude / Codex / Gemini / Antigravity）
- [x] 旧方式の直置き skill / symlink 残骸を特定する
- [x] 設定をバックアップして `ai-config-selector` を現環境に登録する
- [x] legacy skill ディレクトリを削除し、反映結果を検証する

### Progress
- [x] 調査
- [x] 実装
- [x] 検証
- [x] レビュー記録

### Review
- 更新ファイル:
  - `scripts/register.sh`
  - `README.md`
  - `docs/operations.md`
  - `tasks/lessons.md`
  - `tasks/todo.md`
- 実環境で更新した user-facing config:
  - `~/.claude.json`
  - `~/.codex/config.toml`
  - `~/.gemini/settings.json`
  - `~/.gemini/antigravity/mcp_config.json`
- 削除した legacy skill 残骸:
  - `~/.claude/skills`
  - `~/.gemini/skills`
  - `~/.gemini/antigravity/global_skills`
- 実装要約:
  - `scripts/register.sh` に Claude Code (`~/.claude.json`) 対応を追加
  - Codex の登録処理を上書き型から section merge 型に変更し、既存設定を潰さず `ai-config-selector` だけを更新するようにした
  - Gemini / Antigravity / Claude の JSON 設定は merge で `mcpServers.ai-config-selector` を注入するように統一した
- 検証コマンド:
  - `HOME=$(mktemp -d ...) bash scripts/register.sh all` 相当の一時 HOME 検証で Claude/Gemini/Antigravity merge と Codex section 更新を確認
  - `sed -n '1,260p' ~/.claude.json`
  - `sed -n '1,220p' ~/.codex/config.toml`
  - `sed -n '1,220p' ~/.gemini/settings.json`
  - `sed -n '1,220p' ~/.gemini/antigravity/mcp_config.json`
  - `ls -ld ~/.claude/skills ~/.gemini/skills ~/.gemini/antigravity/global_skills`
- 検証結果:
  - `~/.claude.json` は既存の `MCP_DOCKER` を保持したまま `mcpServers.ai-config-selector` が追加された
  - `~/.codex/config.toml` は `ai-config-selector` section が作成された
  - `~/.gemini/settings.json` と `~/.gemini/antigravity/mcp_config.json` は `ai-config-selector` のみを保持している
  - legacy skill ディレクトリ 3 つは削除済み
  - バックアップとして `~/.claude.json.bak.20260309-124350` などの退避ファイルを作成済み
