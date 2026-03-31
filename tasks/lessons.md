# Lessons Learned

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
