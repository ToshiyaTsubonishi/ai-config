# Instruction Files

`instructions/` は AI エージェント向け運用ドキュメントの Git 管理用ディレクトリです。

## Files

- `Agent.md`: Codex 向け運用ルール（同期先: `~/.codex/AGENTS.md`）
- `Gemini.md`: Gemini CLI 向け運用ルール（同期先: `~/.gemini/GEMINI.md`）
- `Lesson.md`: lessons の共有版（同期先: `tasks/lessons.md`）

## Sync

```bash
# 状態確認
bash scripts/sync-instructions.sh status

# 実運用ファイル -> repo に取り込む
bash scripts/sync-instructions.sh pull

# repo -> 実運用ファイルへ反映
bash scripts/sync-instructions.sh push
```

`--dry-run` を付けるとコピーせずに動作確認できます。
