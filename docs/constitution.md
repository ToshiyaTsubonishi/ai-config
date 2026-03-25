# ai-config 憲法

## 1. 使命

ai-config の使命は、**AI agent が正しい Skill / MCP を動的に選べるようにすること**である。
この repo は execution runtime の本体ではなく、**capability selection と planning artifact の control plane** である。

## 2. 中核価値

ai-config の価値は次の領域にある。

1. catalog / registry / selector
2. ranking / retrieval / policy
3. approved plan artifact generation
4. runtime validation / selector-serving
5. vendor provenance / ownership

## 3. 非中核

次は重要だが、中核差別化ではない。

- dispatch runtime の実装詳細
- execution DAG / parallelism / retry
- context handoff runtime
- 外部 runtime ごとの内部都合への追随

これらは boundary 越しに扱い、必要なら別 repo / 別 package へ分離する。

## 4. 基本原則

1. **Selector First**
   Agent にはまず selector を呼ばせる。

2. **Plan as Artifact**
   複雑タスクでは approved plan を先に作る。

3. **Boundary over Internal Coupling**
   execution runtime 連携は stable contract で行う。

4. **Read-Only Runtime**
   serving runtime は build-time index / read-only runtime を守る。

5. **Provenance Matters**
   vendor / import / ownership の正本を崩さない。

## 5. この repo がやること

- Skill / MCP source の正本管理
- ToolRecord 正規化
- index build と runtime validation
- hybrid retrieval / RAG
- selector API / MCP server
- selector-serving deploy surface
- approved plan artifact の生成と検証
- execution boundary の契約定義

## 6. この repo が原則やらないこと

- dispatch runtime を直接 import して内部結合する
- execution engine の詳細を repo の中心に据える
- selector より先に runtime orchestration を最適化する
- vendor ownership を壊してまで runtime convenience を優先する

## 7. 設計判断ルール

新機能は次で判定する。

- これは selection quality を上げるか
- plan artifact を安定させるか
- selector-serving の read-only runtime を強くするか
- それとも runtime 実装詳細を抱え込むだけか

後者なら、boundary の外へ逃がす。

## 8. 成功指標

成功は次で測る。

- 適切な tool / skill を返せるか
- 誤選択率が下がるか
- approved plan の品質が上がるか
- runtime validation が明快か
- serving surface が安定しているか

## 9. リポジトリ構造の原則

概念上は 4 層に分ける。

- **Core**: selector / registry / retrieval / planner / serving
- **Contracts**: approved plan / execution request
- **Vendor**: import / provenance / manifest ownership
- **Runtime boundary**: dispatch adapter and compatibility shim

物理分割は後からでよいが、依存方向は最初から分ける。
