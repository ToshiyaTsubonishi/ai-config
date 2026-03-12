# ai-config 憲法

## 1. 使命

ai-config の使命は、**AI が多くの能力を、適切に、無駄なく、壊さず使えるようにすること**である。
この repo は「道具を増やす箱」ではなく、**AI agent の能力制御プレーン**である。

## 2. 中核価値

ai-config が最も価値を持つのは次の 3 領域である。

1. **catalog / index / selector**
   多数の skill と MCP を、AI が扱える候補集合に整える。

2. **ranking / retrieval / policy**
   何を見せ、何を隠し、通常運用と全件運用をどう切り替えるかを決める。

3. **planning / orchestration**
   1 回の検索で終わらない複雑タスクを、承認可能な plan に落とす。

## 3. 非中核

次は重要だが、ai-config の本質的な差別化領域ではない。

* 外部 repo の取得
* 更新確認
* install / remove UX
* 各 agent の skill path 差異への追随
* 単純な vendor / import 管理

これらは、原則として upstream や既存標準に委譲する。

## 4. 基本原則

1. **Selector First**
   AI には原則として `ai-config-selector` を通じて候補を見せる。
   「全部直読み」は標準運用にしない。

2. **Planning First**
   複雑タスクは、実行より先に plan を作る。
   `plan-only` と `execute-plan` を分ける。

3. **Default is Small, Full is Explicit**
   通常運用は小さく保つ。
   全件探索は意図的な操作でのみ行う。

4. **Direct Install is Exception**
   agent 直インストールは例外扱いとし、メタ層や bootstrap 的な少数 skill に限定する。

5. **Upstream over Reinvention**
   配布・更新・発見の層は、可能な限り upstream を使う。

6. **Catalog before Execution**
   まずカタログに載せる。
   直実行や直登録は、その後で必要性が証明された場合だけ行う。

## 5. この repo がやること

* Skill / MCP を `ToolRecord` に正規化する
* index を構築する
* 検索・ランキングを提供する
* selector として AI へ候補を返す
* plan を作る、検証する
* 承認済み plan を dispatch する
* 実行時の安全性と再現性を担保する

## 6. この repo が原則やらないこと

* すべての外部 skill エコシステムを自前で管理する
* agent ごとに大量の skill を直接配布する
* vendor / install UX を独自実装で抱え込み続ける
* 新しい source / repo を増やすこと自体を成功指標にする

## 7. 例外許容

次は例外として許される。

* always-on の少数 bootstrap skill
* selector の使い方を agent に教えるメタ skill
* planning-first を強制する小さな常駐 policy skill
* 実験のための一時的な直登録

ただし、例外は常に
**「selector / catalog / plan を補助するか」**
で判断する。

## 8. 設計判断ルール

新機能や新しい実装案に対しては、必ず次で判定する。

* これは **AI に正しい道具を選ばせるための機能**か
* それとも **道具を集めたり運んだりするための機能**か

前者なら ai-config に残す価値が高い。
後者なら upstream / 外部ツール / 別レイヤへ逃がす。

## 9. 成功指標

成功は件数ではなく、次で測る。

* AI が適切な tool / skill を選べるか
* 誤選択率が下がるか
* plan の品質が上がるか
* 実行の安全性と再現性が上がるか
* 通常運用でのノイズが減るか

## 10. リポジトリ構造の原則

当面は monorepo を維持する。
ただし、頭の中では次の 3 層に分ける。

* **Core**: catalog / index / selector / ranking / orchestration / dispatch
* **Vendor layer**: source sync / import / update
* **Bootstrap layer**: register / agent 設定反映 / always-on 少数 skill

物理的分割は、責務境界が安定してから行う。
