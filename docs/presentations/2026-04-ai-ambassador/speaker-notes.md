# 2026年4月 AIアンバサダー報告会 speaker notes

## 使い方

- 想定時間は 7 〜 10 分です。
- 各スライドは 3 〜 5 文で読み切れる長さにしています。
- ライブデモが不安定なときは、Slide 12 の静止画補強へすぐ切り替えます。

## Slide 1

今回は ai-config を中心にした成果報告です。  
ポイントは、AI をただ賢くすることではなく、AI agent がその場で使うべき Skill や MCP を選びやすくする基盤を整えたことです。  
この1か月で、selector-serving の公開面、Open WebUI 接続の導線、そして control plane としての説明可能性を整理しました。  
今日はその中身と、Open WebUI でどう見せるかを共有します。

## Slide 2

今月の要約は 3 点です。  
1 つ目は selector-serving を read-only の公開面として整えたこと。  
2 つ目は Open WebUI と MCPO を介した接続テンプレートを repo に持てたこと。  
3 つ目は、ai-config を execution runtime ではなく selector / planner の control plane として説明できる状態にしたことです。

## Slide 3

今回の発表では、実画面だけに頼らず、補助図とライブデモを組み合わせて説明します。  
理由は、見せたい本質が UI の派手さではなく、必要な道具を必要なタイミングで探して使える構造だからです。  
実画面は理解を助けるために使い、補助図で責務分離を固定し、最後にライブデモで接続性を見せる流れにします。

## Slide 4

背景にある課題は 4 つあります。  
Skill や MCP が増えるほど、何を使うべきかの判断が難しくなります。  
さらに候補が増えるとコンテキストが膨らみ、環境差分まで混ざると再現性が落ちます。  
その結果、実行以前に「選定」と「責任分界」がボトルネックになります。

## Slide 5

そこで ai-config は、実行エンジンを全部抱え込むのではなく、道具選びと計画づくりに責務を絞っています。  
まず selector で候補を見つけ、必要なときだけ plan artifact を作り、実行は境界の向こうに渡します。  
この整理により、選定品質、安全性、運用の説明責任を持ちやすくなります。

## Slide 6

この図が全体像です。  
Agent がいきなり何でも実行するのではなく、まず ai-config-selector で候補を取り、その結果から ApprovedPlan を作り、実行は dispatch runtime に渡します。  
この repo の主役は execution runtime ではなく、selector / planner / boundary の 3 つです。  
ここを分けたことで、説明もしやすく、将来の切り離しもしやすくなっています。

## Slide 7

ai-config の中身を分けると、catalog / index、selector、planner artifact、execution boundary、read-only serving の 5 層です。  
単なるツール置き場ではなく、候補を返す質と、その後の進め方を安定させるための control plane と考えると伝わりやすいです。  
エンジニア目線では、provenance と ownership を repo で維持している点も重要です。

## Slide 8

Open WebUI 連携は、Open WebUI から MCPO を見に行き、その先で ai-config-selector-serving の `/mcp` を使う構成です。  
つまり既存 UI に無理なく接続できる形になっています。  
この話を入れる理由は、CLI だけの実験ではなく、実運用の入口を用意できていることを示したいからです。

## Slide 9

デモで見せるポイントは 3 ステップです。  
まず「この依頼に使うべき Skill / MCP を探して」と言わせ、次に候補の詳細を確認し、最後に必要なら downstream MCP の tool list まで見せます。  
ここで見せたいのは、AI が万能であることではなく、道具の選び方が整理されていることです。

## Slide 10

成果としては、公開面の整理、Open WebUI 接続テンプレート、plan と execution の責務分離、ローカルでの readiness 確認まで進められました。  
つまり「設計思想」だけでなく、repo 上のテンプレートと検証手順まで含めて再利用しやすい状態に寄せられています。

## Slide 11

エンジニア向けの価値は 4 つです。  
Selection quality を落としにくいこと、責任分界が明確なこと、provenance / ownership を保てること、そして read-only surface として運用しやすいことです。  
このあたりが、単なる agent 実装との差分として一番伝えたいポイントです。

## Slide 12

ライブデモが不安定でも、このスライドで最低限の証跡を示せます。  
`/healthz` と `/readyz` の応答、Cloud Run / Open WebUI 用テンプレートの存在、ローカル検索の結果をまとめています。  
デモが難しいときは「接続済みの公開面と検証導線はここまで確認できている」と落ち着いて説明すれば十分です。

## Slide 13

今後は候補精度の改善、approved plan の活用、業務ドメインに近い Skill / MCP の拡張を進めます。  
短期では Open WebUI デモを安定運用へ寄せ、中長期では業務知識の agent 化と継続的な棚卸しを回していく想定です。  
要するに、ai-config を「育て続けられる control plane」にしていくのが次のフェーズです。

## ライブデモ固定プロンプト

```text
この依頼に使うべき Skill / MCP を先に探して、理由つきで候補を出してください。
候補のうち一番適切なものの詳細を確認してください。
利用可能な downstream MCP の tool list も確認してください。
```

## デモ失敗時のフォールバック

```text
今日は UI の派手さを見せたいのではなく、必要な道具を必要なタイミングで探して使える構成を見せたいです。
ライブ動作の代わりに、ここでは selector の検索結果、readiness 応答、Open WebUI 接続テンプレートを見せます。
```
