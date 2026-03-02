# AI Kill Switch Protocol (Emergency Stop)

AIの暴走、または予期せぬ市場変動時に、システムを「安全側（Safe Mode）」へ倒すための手順。

## 1. Trigger Criteria (発動条件)
以下のいずれかを検知した場合、**人間の判断を待たずに**自動的にKill Switchを作動させる。
*   **Flash Crash:** 株価や為替が1分間に5%以上変動した場合。
*   **Mass Withdrawal:** 預金流出速度が通常の10倍を超えた場合（デジタル・バンクラン）。
*   **Reputation Hazard:** SNS上で「SBIのAIが差別発言をした」という投稿が1万リポストを超えた場合。

## 2. Execution Steps (遮断手順)
1.  **Stop Inference:** UMGのルーティングを停止し、全てのAIリクエストを「現在メンテナンス中です」という静的レスポンスに切り替える。
2.  **Freeze Assets:** MPCウォレットの署名権限を凍結し、新規の出金を物理的にブロックする。
3.  **Alert:** CEO、CTO、CRO（リスク責任者）、および金融庁担当者へ自動通報する。

## 3. Recovery (復旧)
*   **Root Cause Analysis:** ログ（Audit Log）を解析し、原因が「AIのハルシネーション」か「外部攻撃」かを特定する。
*   **Rollback:** 問題のあるモデルバージョンを切り離し、安定版（Previous Stable）へロールバックする。
*   **Human Approval:** CROの電子署名をもって、サービス再開を許可する。

