# Lessons Learned

## 2026-03-03: ai-config-dispatch とai-config-selector の活用

### ミス 1: ai-config-dispatch を使用しなかった

- **状況**: ユーザーが `ai-config-dispatch "..."` 形式でプロンプトを送信した
- **期待動作**: `ai-config-dispatch` CLI を実行して Codex/Gemini CLI に作業を分散する
- **実際の動作**: dispatch を無視して直接作業してしまった
- **ルール**: プロンプトが `ai-config-dispatch` で始まる場合、必ず dispatch システムを通じてマルチエージェントで作業する。自分（Antigravity）はオーケストレーターとして振る舞い、計画・実行・検証を監督する。

### ミス 2: ai-config-selector で検索しなかった

- **状況**: ai-config-selector の MCP ツール (`search_tools`) が利用可能だった
- **期待動作**: タスク開始時に `search_tools` で関連スキル / MCP を検索する
- **実際の動作**: 一切検索せず直接作業した
- **ルール**: タスク開始時に必ず `search_tools` で関連ツールを検索する。結果がなくても検索すること自体が正しい動作。見つかったスキルがあれば活用する。

### ミス 3: Gemini API の response.content が list を返すケースを未考慮

- **状況**: `response.content` が `str` であることを前提にしていたが、Gemini API は multi-part content の場合 `list` を返す
- **影響**: `'list' object has no attribute 'strip'` で LLM プランニングが毎回フォールバックに落ちていた
- **修正**: `_extract_text()` ヘルパー関数を追加。`list` の場合は各パーツの `.text` を結合する
- **ルール**: LLM レスポンスの `content` フィールドは常に `str | list` の両方をハンドルする

## 2026-03-09: Managed MCP は selector-first を守る

### ミス 1: managed MCP を user-facing config に直接追加した

- **状況**: `config/master/ai-sync.yaml` に `raindrop` を追加した際、検索対象として index 化するだけでなく、Codex / Gemini / Antigravity の実設定にも直接 `raindrop` を追記した
- **期待動作**: `ai-config-selector` から選択できる managed MCP として登録し、ユーザーが明示的に求めない限り各クライアントの直接 MCP 設定は増やさない
- **実際の動作**: `~/.codex/config.toml`, `~/.gemini/settings.json`, `~/.gemini/antigravity/mcp_config.json` に `raindrop` を直接登録してしまった
- **ルール**: managed MCP の追加時は「selector の catalog 追加」と「各クライアントへの直接登録」を分けて考える。明示要求がない限り、user-facing config には `ai-config-selector` だけを残す

## 2026-03-09: 環境セットアップでは Claude と legacy skill 残骸も確認する

### ミス 1: user-facing config の対象から Claude を外して考えていた

- **状況**: 環境セットアップ対象を Codex / Gemini / Antigravity に寄せて考え、`~/.claude.json` を確認していなかった
- **期待動作**: 実環境セットアップでは `~/.claude.json`, `~/.codex/config.toml`, `~/.gemini/settings.json`, `~/.gemini/antigravity/mcp_config.json` を最初に確認する
- **実際の動作**: Claude Code の設定ファイルを後から見つけて対象に追加した
- **ルール**: ローカル AI ツール設定を触るときは、まず Claude / Codex / Gemini / Antigravity の実ファイル位置を確認してから作業する

### ミス 2: legacy skill symlink ディレクトリを setup 対象として先に考慮していなかった

- **状況**: `~/.claude/skills`, `~/.gemini/skills`, `~/.gemini/antigravity/global_skills` に旧方式の symlink skill が残っていた
- **期待動作**: 現在の selector-first 運用では直置き skill は不要なので、環境セットアップ時に残骸として確認・削除する
- **実際の動作**: ユーザー指摘後に cleanup 対象として扱った
- **ルール**: user-facing config をセットアップする際は、設定ファイルだけでなく legacy skill ディレクトリの残骸有無も確認する
