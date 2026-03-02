# 本番環境デプロイメントログ (Deployment Log)

**サービス名:** ____________________
**バージョン:** v__.__.__
**実施日:** 202_/__/__ __:__ - __:__
**実施者:** ____________________
**承認者:** ____________________

## 1. 事前確認 (Pre-Flight Check)
- [ ] **CI Status:** 全テストがPassしていること (Commit Hash: ________)
- [ ] **Backup:** DBのバックアップ取得完了
- [ ] **Communication:** ユーザーへのメンテナンス告知完了
- [ ] **Risk:** ロールバック手順の確認

## 2. 作業ログ (Execution)
| 時間 | 操作内容 | 結果 | 担当 |
| :--- | :--- | :--- | :--- |
| 10:00 | Terraform Apply | Success | admin |
| 10:10 | DB Migration | Success | admin |
| 10:15 | Application Deploy | Success | admin |
| | | | |

## 3. 動作確認 (Verification)
- [ ] **Smoke Test:** 重要機能（ログイン、決済等）が動作するか
- [ ] **Monitoring:** エラーレート、レイテンシに異常がないか

## 4. 完了判定
- [ ] 作業完了 / 切り戻し (Rollback)

**特記事項:**
(トラブルや想定外の挙動があれば記載)
