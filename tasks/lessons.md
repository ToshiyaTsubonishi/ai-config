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
