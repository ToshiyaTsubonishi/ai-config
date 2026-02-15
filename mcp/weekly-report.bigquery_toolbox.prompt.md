# Weekly Report Prompt Template (for `bigquery_toolbox`)

Use this prompt in Codex with the `bigquery_toolbox` MCP server enabled.

---

以下の条件で、BigQuery から週次マーケレポートを作成してください。  
必ず `bigquery_toolbox` のツールを使って実データを取得し、推測で埋めないこと。

## Parameters
- Project: `{{PROJECT_ID}}`
- Week start (inclusive): `{{WEEK_START_YYYY-MM-DD}}`
- Week end (inclusive): `{{WEEK_END_YYYY-MM-DD}}`
- Prior week start: `{{PRIOR_WEEK_START_YYYY-MM-DD}}`
- Prior week end: `{{PRIOR_WEEK_END_YYYY-MM-DD}}`
- GA4 events table: `{{PROJECT_ID}}.{{GA4_DATASET}}.events_*`
- Optional ad cost table: `{{PROJECT_ID}}.{{COST_DATASET}}.{{COST_TABLE}}`

## Required metrics
1. Sessions
2. Users
3. Conversions (`purchase` or `generate_lead`, whichever exists)
4. CVR = Conversions / Sessions
5. Top channels by sessions
6. Top landing pages by sessions
7. WoW change (%) for Sessions, Conversions, CVR

## Tool workflow (must follow)
1. `list_dataset_ids` and `list_table_ids` で対象データセット/テーブル存在確認
2. `execute_sql` で今週・先週の指標を取得
3. 定義が曖昧な場合は SQL 内で明示（例: conversion event の定義）
4. 数値の整合をチェックし、異常値があれば注記

## Output format
以下のMarkdownで出力:

### 1) Weekly KPI Summary
- Sessions: X (WoW: Y%)
- Users: X (WoW: Y%)
- Conversions: X (WoW: Y%)
- CVR: X% (WoW: Ypt)

### 2) Channel Breakdown
テーブル: Channel | Sessions | Share | WoW

### 3) Top Landing Pages
テーブル: Landing Page | Sessions | Conversions | CVR

### 4) Key Insights (max 5)
- 箇条書きで、数字付きの示唆のみ

### 5) Next Actions (max 5)
- 来週実行すべき施策を優先順で

### 6) SQL Appendix
- 実行した主要SQLをそのまま掲載

## Notes
- 文字列比較は大小文字ゆれを考慮
- 可能な限り `SAFE_DIVIDE` を使用
- タイムゾーンは `Asia/Tokyo` で揃える
