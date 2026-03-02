# スキル検証チェックリスト (Validation Checklist)

**対象スキル:** ____________________
**検証日:** 202_/__/__

## 1. 静的解析 (Static Analysis)
- [ ] ディレクトリ構造は `gemini-skill-creator` の基準（SKILL.md, assets/, references/, scripts/, agents/）を満たしているか？
- [ ] `SKILL.md` の記述は具体的かつ命令形か？

## 2. 動的検証 (Dynamic Testing)
- [ ] `/skills reload` でスキルを呼び出した際、エラーなくInstructionsが表示されるか？
- [ ] 指示に従ってタスクを実行した際、想定通りの成果物（ファイル）が生成されるか？
- [ ] リソース (assets/, references/, scripts/, agents/) のリンク切れやパス間違いはないか？

## 3. 安全性 (Safety)
- [ ] 危険なコマンド（システム領域へのアクセス等）が含まれていないか？