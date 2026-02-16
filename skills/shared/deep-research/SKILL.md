---
name: deep-research
description: Web調査を複数ステップで実行し、出典付きの調査レポートを作成する。deep-researcher-mcp の代替運用に使う。
---

# Deep Research

MCPを使わずに、エージェントのWeb調査能力で調査レポートを作成します。

## Workflow

1. 調査目的と評価軸を明確化
2. 一次情報を優先して収集（公式文書・一次ソース）
3. 複数ソースでクロスチェック
4. 事実/推論を分離して要約
5. 出典リンク付きで最終レポート化

## Output

- `summary`: 結論要約
- `findings`: 主要論点
- `evidence`: 出典付き根拠
- `open_questions`: 未確定事項

## Guardrails

- 推測は必ず推測と明示する
- 日付が重要な情報は具体日付で記載する
