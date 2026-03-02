---
name: data-normalization-playbook
description: 非構造テキストを customer/corporation/transaction/artwork/artist 形式へ正規化する手順を提供する。data-normalizer-mcp の代替運用に使う。
---

# Data Normalization Playbook

MCP不要で、入力テキストを扱いやすい構造データへ落とすための手順書スキルです。

## Supported Schemas

- `customer`
- `corporation`
- `transaction`
- `artwork`
- `artist`

## Workflow

1. 入力の粒度を確認（人・法人・取引・作品・作家）
2. 欠損値と曖昧値を抽出
3. 目標スキーマにマッピング
4. JSONとして正規化結果を出力
5. 検証ポイント（必須キー不足、型不一致）を併記

## Output Format

- `normalized`: 正規化済みJSON
- `missing_fields`: 欠損フィールド一覧
- `assumptions`: 補完した仮定

## Guardrails

- 不明値は推測で埋めず `null` と `assumptions` に分離
- 個人情報は最小限の項目のみ保持
