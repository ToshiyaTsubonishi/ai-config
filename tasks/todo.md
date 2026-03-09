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
