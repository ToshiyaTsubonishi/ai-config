# Regional Bank AGI Replication Kit

地銀DXを「開発プロジェクト」から「導入プロジェクト」へ変えるためのキット。

## 1. Concept: "BaaS on AGI"
地銀は「UI（アプリ）」と「顧客基盤」のみを提供する。
裏側の「知能（AI）」と「商品（金融機能）」はSBIがAPI経由で提供する。

## 2. Integration Steps (3 Months)

### Month 1: Configuration
- **Parameter Tuning:** `tenant_config.json` に銀行名、トーン＆マナー（方言対応など）、提供機能（投資の有無）を記述する。
- **Brand Assets:** ロゴ画像とブランドカラー（CSS変数）を差し替える。

### Month 2: Connection
- **API Binding:** 地銀側の勘定系API（残高照会・振込）とUMGのアダプターを接続する（VPN/専用線）。
- **Data Ingestion:** 地銀の独自商品（定期預金、住宅ローン）のパンフレットPDFをRAGに学習させる。

### Month 3: Rehearsal
- **Employee Beta:** 行員100名によるドッグフーディングと、ガードレール（誤回答ブロック）の調整。
- **Go Live:** 全顧客へリリース。

## 3. Financial Model
- **Initial Cost:** 0円（開発費不要）。
- **Running Cost:** 月額固定費 + APIコール従量課金。
- **Revenue Share:** SBI証券/損保への送客手数料（キックバック）。

