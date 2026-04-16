# Lessons Learned

## 2026-04-15: 制限付き production は prebuilt digest と release manifest を先に固める

### ミス 14: staging が動いたあとも production の build/auth 制約を同じ熱量で固定していなかった

- **状況**: staging stack は runtime/E2E まで通ったが、production 環境では `docker login` / `gcloud auth` / GitHub login ができないという制約が後から明示された
- **期待動作**: 本番 deploy に進む前に、別の build-capable environment で selector/provider image を publish し、`@sha256:` の digest ref と commit/bundle provenance をまとめた release manifest を先に用意する
- **実際の動作**: staging までは local build / gcloud / GUI の導線が中心で、production の zero-auth deploy path はまだ固定されていなかった
- **ルール**: 企業環境の production で auth/build 制約がある場合は、Cloud Run 設定より先に `prebuilt GHCR image + pinned digest + release manifest + temporary package visibility rule` を定義する。deploy guide には tag ではなく digest ref を主系として書く

## 2026-04-15: Open WebUI の tool server 検証だけでは chat E2E は保証されない

### ミス 12: tool server 2 接続が見えても、chat model provider が無いと E2E が止まる

- **状況**: staging Open WebUI で `TOOL_SERVER_CONNECTIONS` は正しく 2 件入り、`/api/v1/tools/` でも `server:ai-config-mcpo` / `server:ai-config-provider-mcpo` が見えていたが、`/api/models` は空だった
- **期待動作**: Open WebUI で selector/provider の tool flow を chat まで検証したいなら、tool server 配線と同時に conversation model provider も render/deploy に含める
- **実際の動作**: 当初の staging manifest は `GEMINI_API_KEY` だけ渡しており、OpenAI-compatible Gemini endpoint (`OPENAI_API_BASE_URLS` / `OPENAI_API_KEYS`) を設定していなかったため、tool server の存在確認までは通っても chat E2E は実行できなかった
- **ルール**: Open WebUI staging を phase 完了に進めるときは、`tool server visibility` と `chat model availability` を別物として確認する。`/api/v1/configs/tool_servers` と `/api/models` の両方が埋まってから E2E を始める

## 2026-04-15: Cloud Run の public probe path と internal liveness は分けて観測する

### ミス 13: public `/healthz` 404 を見て route 未実装だと即断しやすい

- **状況**: staging selector/provider の public HTTPS `/healthz` は Google Frontend で 404 だったが、Cloud Run の internal liveness probe と container logs では `/healthz` が 200 を返していた
- **期待動作**: Cloud Run probe path の検証では、public curl 結果と container logs / probe logs を両方見て、app 自体の route と edge での挙動を分けて判断する
- **実際の動作**: 最初は public 404 だけを見て contract break と見なしそうになったが、実際には internal liveness は成功していた
- **ルール**: Cloud Run の health/readiness mismatch を見たら、`public curl`, `gcloud logging read` の probe log, `latestReadyRevisionName` を必ずセットで確認する。public contract が必要か、internal probe 成功で十分かを分けて結論を出す

## 2026-04-15: GCP staging は runtime/E2E と provenance を揃えるまで完了扱いにしない

### ミス 11: staging 実装と静的検証が通っても、runtime verification 前に完了感を出しやすい

- **状況**: separate-project staging stack の renderable assets とローカル tests は green だったが、`gcloud` 未認証のため actual Cloud Run deploy / `/readyz` / OpenAPI / Open WebUI E2E は未実施だった
- **期待動作**: GCP staging の task は、Cloud Run への実 deploy、runtime health/readiness、MCPO OpenAPI、Open WebUI tool server 可視化、selector/provider/E2E 実測まで揃って初めて phase 完了とみなす
- **実際の動作**: 実装承認が出た時点で構成面は前進していたが、runtime evidence が無いまま次フェーズへ進みそうになった
- **ルール**: Cloud Run / GCP staging の作業では、`code green` と `runtime green` を分けて扱う。さらに staging でも最初から image ref、commit SHA、provider-bundle version を revision annotation か `/readyz` で追えるようにしてから deploy に入る

## 2026-04-03: Eval CLI の可変引数は metric contract と一致させる

### ミス 10: `--top-k` を可変に見せつつ metric の一部を固定深さのままにした

- **状況**: retrieval eval CLI に `--top-k` を追加したが、実装では `top_k=max(args.top_k, 5)` としつつ、`mrr` の加算も `rank <= 5` のときだけ行っていた
- **期待動作**: 可変の search depth を exposed するなら、metric 側もその深さと整合させる。少なくとも `MRR` は `top_k` 内で見つかった rank 全体を使って計算する
- **実際の動作**: `--top-k 10` で expected tool が 8 位でも rank 自体は取れるのに、`MRR` では 0 扱いになる不自然な contract になっていた
- **ルール**: Eval / benchmark CLI では、公開オプションの意味と metric 計算を必ず一致させる。固定深さの metric を出すなら引数も固定化するか最小値を明示し、case file の参照 ID は typo を metric 劣化に混ぜず fail fast で弾く

## 2026-03-31: prebuilt image 前提でも local Docker path を書く

### ミス 8: guide に「事前に image を用意する」だけ書いて手元 Docker の導線を省いた

- **状況**: GCP GUI guide を enterprise 制約に合わせて prebuilt image 前提へ直したが、ユーザー側では local Docker が使える状況だった
- **期待動作**: `GitHub 連携なし / gcloud なし` でも local Docker が使えるなら、`docker build` から `docker tag` / `docker push` までの最短導線を guide にそのまま書く
- **実際の動作**: 「事前に image URL を用意する」とだけ書いたため、どこで何を build / push すればよいかが途中でわかりにくくなった
- **ルール**: deploy guide で prebuilt image を前提にするときも、local Docker があり得るなら `build -> tag -> push -> Cloud Run に貼る` の具体コマンドと、GHCR / Artifact Registry の典型的な権限エラーを必ず併記する

## 2026-03-31: GHCR troubleshooting は namespace と Docker credsStore を先に見る

### ミス 9: GHCR の denied を token scope だけの問題だと見なしやすい

- **状況**: `write:packages` を付けても GHCR push が `denied` で失敗し、さらに `docker login` では `docker-credential-desktop` missing が出た
- **期待動作**: GHCR では `gh auth status` の scope だけでなく、`gh api user --jq '.login'` で実際の login 名を確認し、その namespace に push する。加えて `~/.docker/config.json` の `credsStore` が壊れていないかを見る
- **実際の動作**: 最初は repo owner ベースの `ghcr.io/ToshiyaTsubonishi/...` を試し、認証済み account `tsytbns` の namespace との差を見落とした。Docker 側も `credsStore: "desktop"` の helper 不在で login が保存できなかった
- **ルール**: GHCR push で `denied` が出たら、まず `gh auth status` の `write:packages`、次に `gh api user --jq '.login'` と push 先 namespace、最後に `~/.docker/config.json` の credential helper を確認する。helper 欠落時は一時 `DOCKER_CONFIG` で回避する

## 2026-03-31: デプロイ guide では enterprise 制約を最初に固定する

### ミス 7: GUI guide で GitHub 連携と `gcloud` 利用を暗黙に前提化した

- **状況**: GCP GUI セットアップガイドを書いたが、Cloud Build trigger のために GitHub を GCP に接続し、必要に応じて `gcloud` を使える前提が混ざっていた
- **期待動作**: 会社環境の制約がありそうなセットアップ文書では、最初に「CLI が使えるか」「GitHub / 外部 SCM を GCP に接続できるか」「どのレジストリが使えるか」を固定し、不可なら prebuilt image 前提の手順に切り替える
- **実際の動作**: 最初の guide は個人開発寄りの前提を含み、企業環境ではそのまま辿れない導線になっていた
- **ルール**: デプロイ / セットアップガイドを書くときは、冒頭で `CLI可否 / SCM連携可否 / レジストリ制約` を明文化する。どれかが不可なら、GCP 内 build を主ルートにせず、`事前に用意した image を GUI で載せる` 方式を第一候補にする

## 2026-03-03: ai-config-dispatch とai-config-selector の活用

### ミス 1: ai-config-dispatch を使用しなかった

- **状況**: ユーザーが `ai-config-dispatch "..."` 形式でプロンプトを送信した
- **期待動作**: `ai-config-dispatch` CLI を実行して Codex/Gemini CLI に作業を分散する
- **実際の動作**: dispatch を無視して直接作業してしまった
- **ルール**: プロンプトが `ai-config-dispatch` で始まる場合、必ず dispatch システムを通じてマルチエージェントで作業する。自分（Antigravity）はオーケストレーターとして振る舞い、計画・実行・検証を監督する。

### ミス 2: ai-config-selector で検索しなかった

- **状況**: ai-config-selector の MCP ツール (`search_tools`) が利用可能だった
- **期待動作**: タスク開始時に `search_tools` で関連スキル / MCP を検索する
- **実際の動作**: 一切検索せず直接作業した
- **ルール**: タスク開始時に必ず `search_tools` で関連ツールを検索する。結果がなくても検索すること自体が正しい動作。見つかったスキルがあれば活用する。

### ミス 3: Gemini API の response.content が list を返すケースを未考慮

- **状況**: `response.content` が `str` であることを前提にしていたが、Gemini API は multi-part content の場合 `list` を返す
- **影響**: `'list' object has no attribute 'strip'` で LLM プランニングが毎回フォールバックに落ちていた
- **修正**: `_extract_text()` ヘルパー関数を追加。`list` の場合は各パーツの `.text` を結合する
- **ルール**: LLM レスポンスの `content` フィールドは常に `str | list` の両方をハンドルする

## 2026-03-11: 読み取り専用の複数観点検証でも dispatch を使う

### ミス 4: repo inspection / validation を direct 実行してしまった

- **状況**: Windows setup / MCP registration / downstream MCP / instruction sync のように複数の観点を横断する読み取り専用タスクを受けた
- **期待動作**: `ai-config-selector` で候補を確認したうえで、`.venv\Scripts\ai-config-dispatch.cmd` を使って検証を分担し、証拠を集約する
- **実際の動作**: 読み取り専用だから trivial と判断して direct に調査してしまった
- **ルール**: 読み取り専用でも、2つ以上の観点・サブシステムを横断する repo inspection / setup validation / MCP validation は非自明タスクとして dispatch を優先する

## 2026-03-12: 観測 API の契約は最初に固定する

### ミス 5: observability の severity と JSON 互換性を後から補強する形になった

- **状況**: vendor observability の実装計画に対して、`unmanaged_local` の doctor 扱いと `status --json` の安定 schema が後から明文化された
- **期待動作**: local state を返す観測 API では、実装前に severity と JSON contract を固定する
- **実際の動作**: 初期実装案では `extra_local` と `unmanaged_local` の扱い差、`schema_version` / `generated_at` を明示していなかった
- **ルール**: 新しい observability/status API を追加するときは、実装前に「どの状態が fail/pass か」と「JSON schema version / generation timestamp」を必ず決めてから着手する

## 2026-03-27: local / GitHub 競合は merge 状態と index まで確認する

### ミス 6: working tree だけ見て remote 競合の実態を過小評価しやすい

- **状況**: ユーザーから「ローカル最新と GitHub 最新が衝突しているかもしれない」と指摘を受けた
- **期待動作**: `git status`、`git diff --cached --name-status`、`.git/MERGE_HEAD` まで見て、未コミット差分だけでなく staged remote changes / merge in progress を先に把握する
- **実際の動作**: 初見では working tree の modified files だけ見えて、merge 途中であることと staged 側の大量差分を後から掴んだ
- **ルール**: local と GitHub の統合作業では、最初に `git status` と `git diff --cached --name-status` と `MERGE_HEAD` の有無を必ず確認し、conflict marker 混入ファイルも検索してから統合方針を決める

## 2026-04-16: release workflow は clean checkout 前提で index を自前生成する

### ミス 10: local にある `.index` を暗黙前提にして GHCR publish workflow を組んだ

- **状況**: `publish-ghcr-release.yml` を GitHub Actions で動かしたところ、`ai-config-provider` の bundle materialization が `ai-config/.index/records.json` 不在で落ちた
- **期待動作**: release script / workflow は clean checkout でも完結し、local で生成済みの index や artifact に依存しない
- **実際の動作**: local では `.index` が残っているため見えなかったが、CI では clean checkout のため provider bundle 生成前に必要な selector index が無かった
- **ルール**: repo 外部へ publish する build/release workflow は、clean checkout で必要 artifact を全部自前生成する。特に provider bundle のように `.index/records.json` を読む処理がある場合は、release script 側で bootstrap を持つか、workflow に明示的な build step を入れる
