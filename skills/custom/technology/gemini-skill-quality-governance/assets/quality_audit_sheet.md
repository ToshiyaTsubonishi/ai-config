# スキル品質監査シート (Quality Audit Sheet)

**対象スキル:** ____________________
**監査人:** GEMINI-Skill-Quality-Governance

## 1. 構造 (Structure)
- [ ] **SKILL.md**: 必須セクション（Overview, Instructions）が存在する。
- [ ] **Directory**: `assets/` や `references/` が適切に整理されている。
- [ ] **Metadata**: YAMLフロントマター（name, description）が正しく記述されている。

## 2. 内容 (Content)
- [ ] **具体性**: 「よしなにやる」ではなく「XXファイルを作成する」と書かれている。
- [ ] **安全性**: 危険なコマンド（`rm -rf /` 等）を誘発する記述がない。
- [ ] **独立性**: 他のスキルがなくても（あるいは明示された依存関係があれば）動作する。

## 3. ユーザビリティ (Usability)
- [ ] **可読性**: 箇条書きやコードブロックが使われ、読みやすい。
- [ ] **テンプレート**: ユーザーが入力を楽にするためのテンプレートが用意されている。

**総合判定:**
[ Pass / Conditional Pass / Fail ]
