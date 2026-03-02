# 銀行実務（個人・法人）高度化マニュアル

## 1. AI審査・モデルガバナンス (Retail Loan)
- [ ] **Explainability (XAI)**: SHAP値等を用い、審査結果の寄与変数を可視化できているか。
- [ ] **Fairness Audit**: 属性（年齢、居住地域等）による差別的判定の有無を独立検証済みか。
- [ ] **Drift Monitoring**: 入力データの傾向変化を検知し、AIモデルのリトレーニングを月次で検討しているか。

## 2. BaaS / Embedded Finance 連携要件
- **API Security**: mTLS（相互TLS）およびOAuth2.0による認証・認可の徹底。
- **Compliance Integration**: 提携先画面内でのeKYC（本人確認）および意向把握プロセスの完結。
- **SLA**: 提携プラットフォームのサービス停止時におけるフォールバック（代替）手段の確保。

## 3. 法人ソリューション & 事業承継 (Corporate)
- [ ] **CMS (Cash Management System)**: グループ会社間の資金一元管理による利息効率化の提案。
- [ ] **Transaction Banking**: 振込手数料および外貨両替コストの動的最適化。
- [ ] **Business Succession**: 信託機能を活用した「自社株の集約・移転」スキームの策定。

## 4. 途上与信 & 債権管理
1. **Real-time Monitoring**: 口座入出金データおよび外部信用情報の変化を日次で突合。
2. **Predictive Alert**: 「給与振込の停止」や「他社借入の急増」を検知し、限度額を自動制御。
3. **Automated Collection**: 初期延滞者への自動IVR（音声）およびSMSによるリマインド。
