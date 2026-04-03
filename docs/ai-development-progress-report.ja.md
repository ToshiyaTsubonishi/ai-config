# ai-config AI開発活動 経過報告メモ

## まず一言で

今回の活動で整備しているのは、AI をただ賢くする仕組みではなく、**AI agent がその場で使うべき Skill / MCP を選び、必要なら計画を作って、安全な境界の向こうに実行を渡すための control plane** です。

言い換えると、

> ai-config は「AI の実行エンジン」ではなく「AI の道具選びと実行前整理を担う基盤」です。

## 30秒で話すなら

AI 活用では、ツールを増やすこと自体よりも、「どの場面でどの Skill や MCP を使うべきかを間違えないこと」が難しくなります。  
ai-config はそこを担う仕組みです。Skill / MCP を catalog 化して index を作り、agent からは selector として呼び出せるようにしています。必要なときだけ候補を返し、必要なら approved plan を作り、実行そのものは dispatch runtime に boundary 越しで渡します。  
そのため、コンテキストの無駄遣いを減らしつつ、選定品質、運用性、責任分界を保ちやすい構成になっています。

## 3分版の説明

AI 開発を進めると、Skill や MCP を増やすのは比較的簡単です。  
ただ、数が増えるほど agent 側では「何を使うべきか」が分かりにくくなり、不要な候補も増えて、選定ミスやコンテキスト肥大化が起きやすくなります。

ai-config は、その問題に対して「全部を事前に抱え込ませる」のではなく、**必要なときに必要な候補だけを出す**方向で設計されています。  
この repo の主役は execution runtime ではなく、次の 3 つです。

1. Skill / MCP の catalog と index
2. selector による候補検索と詳細確認
3. approved plan という計画 artifact の生成と検証

逆に、DAG 実行、retry、並列実行、context handoff のような runtime の重い責務は dispatch 側に分けています。  
つまり、`ai-config` は「何を使うか」と「どういう計画で進めるか」を安定して扱い、実行の細かい都合は別境界へ逃がしている、という整理です。

この分け方のメリットは 3 つあります。

1. agent に全部の知識を押し込まなくてよいので、選定品質が下がりにくい
2. selector-serving を read-only で運用できるので、公開面を安全に保ちやすい
3. execution runtime を将来別 repo / 別 package にしても、ai-config 側の責務がぶれにくい

## エンジニア向けに伝わりやすいポイント

- これは「AIのための capability broker」であり、単なるツール置き場ではない
- 価値の中心は runtime の派手さではなく、selection quality と planning quality にある
- provenance / ownership を repo できちんと管理している
- selector-serving は read-only runtime として Cloud Run に載せやすい
- execution は stable boundary 越しに dispatch へ渡すので、責任分界が明確

## Open WebUI デモの見せ方

今回のデモは、Open WebUI 上で「ai-config が MCP として実際に使える」ことを見せる形が分かりやすいです。  
構成としては次です。

```text
Open WebUI
  -> MCPO
  -> ai-config-selector-serving (/mcp)
  -> search_tools / get_tool_detail / downstream MCP bridge
```

repo には Cloud Run 用のテンプレートとして次が入っています。

- `deploy/cloudrun/ai-config-selector.service.yaml`
- `deploy/cloudrun/ai-config-mcpo.service.yaml`
- `deploy/cloudrun/open-webui.service.mcpo.yaml`
- `deploy/cloudrun/open-webui.tool-server-connections.example.json`

### デモ中の言い方

「今日は AI が何でも知っていることを見せたいのではなく、必要な道具を必要なタイミングで探して使える状態を見せたいです」

この一言を先に置くと、デモの意図が伝わりやすくなります。

### デモ手順のおすすめ

1. Open WebUI に ai-config の tool server が入っている画面を見せる
2. 「この相談に使うべき Skill / MCP を探して」と自然言語で依頼する
3. `search_tools` が動いて候補が出る様子を見せる
4. 「その候補の詳細も見て」と依頼し、`get_tool_detail` を使わせる
5. 可能なら downstream MCP の tool list まで見せる

### デモ用の言い回し例

「たとえば agent に『Next.js の最新仕様を調べたい』と投げたときに、最初から全部のツールを抱え込ませるのではなく、まず何を使うべきかを selector で見つけます。ここで ai-config が効いています」

### 失敗しにくいデモプロンプト

- 「この依頼に使うべき Skill / MCP を先に探して、理由つきで候補を出してください」
- 「候補のうち一番適切なものの詳細を確認してください」
- 「利用可能な downstream MCP の tool list も確認してください」

この順番にすると、検索、詳細確認、接続性の 3 点を無理なく見せられます。

## その場で読み上げられる発表原稿

今回の ai-config でやっていることを一言でいうと、AI agent のための道具選びの基盤づくりです。  
AI 活動では、モデルやツールを増やすこと自体は比較的簡単ですが、本当に難しいのは、その場でどの Skill や MCP を使うべきかを間違えずに選ぶことです。  
ai-config はそこに焦点を当てています。Skill / MCP を catalog 化して index を作り、agent はまず selector を呼んで候補を見つけます。必要な場合だけ plan を作り、実行そのものは dispatch runtime に渡します。  
なので、この repo は実行エンジン本体というより、選定、計画、責任分界を扱う control plane です。  
今回のデモでは、Open WebUI から MCP として ai-config を登録し、実際に候補検索と詳細確認が動くところを見せます。これによって、単なる構想ではなく、既存の UI から使える形で統合できていることを示したいと思っています。

## 想定Q&A

### Q. これって普通の agent 実装と何が違うのですか

A. agent 本体を賢くするというより、agent が使う Skill / MCP の選定と計画生成を外出しして、そこを安定した基盤として扱っている点です。

### Q. なぜ全部のツールを最初から読み込ませないのですか

A. 数が増えるほどコンテキストを圧迫し、不要な候補も混ざり、選定品質が下がるからです。必要時に必要な候補だけ返すほうが運用しやすいと考えています。

### Q. なぜ dispatch を分けているのですか

A. 実行 runtime は並列実行や retry など変化が多く、責務も重いためです。ai-config は selector / planner に集中し、execution は stable boundary 越しに別責務へ渡す設計です。

### Q. Open WebUI デモの意味は何ですか

A. CLI だけでなく、既存の UI に MCP / tool server として接続できることを見せられる点です。つまり、運用現場で触れる形になっていることを示せます。

### Q. 今どこまで動いていますか

A. repo には selector-serving、Cloud Run 用テンプレート、Open WebUI + MCPO の接続テンプレートがあり、ローカルでは selector-serving の `/healthz` と `/readyz` 応答を確認できています。

## 避けたほうがよい言い方

- 「AIが全部自動でやってくれます」
- 「何でもできる基盤です」
- 「runtime も planner も全部ここでやっています」

代わりに、次の言い方が安全です。

- 「必要な道具を選びやすくする基盤です」
- 「実行そのものではなく、選定と計画に強みがあります」
- 「UI から実運用できる形に寄せています」
