# ELタイムズ HTML 変換ルール

## ■ 基本仕様

- HTML ファイルの文字コードは **UTF-8**、改行コードは **LF** とします。
- 最大の見出しは **H3**、以下は H4 → H5 → H6 の順とします。
- 段落先頭にある全角スペース `　` は削除してください。
-  `<b>` （太字強調）は重要です。絶対に省略せず、すべて `<strong>` でマークアップしてください。

## ■ 全体構造
`assets/el_times_template.html` をベースに使用してください。
抽出された記事コンテンツは、テンプレート内の `<!-- CONTENT_START -->` と `<!-- CONTENT_END -->` の間に挿入します。
ヘッダー、フッター、CSSリンク、および body クラス (`times kininaru`) はテンプレートのものを維持してください。

## ■ 許可される HTML タグ
`strong, table, thead, tbody, tfoot, tr, th, td, ul, ol, li, p, h3, h4, h5, h6, img, section`
※ `div` は特定のクラス（`resume`, `column_text`, `scrollTable` 等）のラッパーとしてのみ許容。
※ `span, em, blockquote, font` は禁止。

## ■ 見出し・強調
- 段落全体が太字の場合は見出し（H3, H4...）とみなします。
- 表のセルの文言がすべて太字の場合は `<th>` を使用してください。

## ■ 段落
- 原則として `<p>` を使用してください。段落内での `<br>` は禁止です。

## ■ リスト変換
- Word 内の箇条書きは `<ul><li>〜</li></ul>` に変換してください。
- リストを開始したら必ず `<ul>` を開き、終了時には必ず `</ul>` を閉じてください。

## ■ テーブル変換
- `<table>` は必ず以下の構造でラップしてください（スクロール対応）。
  ```html
  <div class="scrollTable" data-scroll="horizontal"><div data-guide="scroll"><table class="tab">
  ```
- `<tbody>` は必須。終了時は `</tbody></table></div></div>` の順で閉じてください。

## ■ 画像の取り扱い
- **形式**: `<img alt="Altテキスト" class="column_image" src="/unified/images/articles/times/kininaru/{Issue号}/{連番}.jpg"/>`
  - `{Issue号}`: 指定された番号（例：80）
  - `{連番}`: 出現順に `01`, `02`, `03` ...
- **属性**: `alt` には画像のキャプション（コメントから抽出）を入れます。
- **配置**: 画像を `<p>` タグで囲まないでください。
- **Resumeクラス**: 画像の直後に出現する段落には、必ず `<p class="resume">` を付与してください。

## ■ 画像一覧（末尾）
- ファイルの最後に、以下の形式で Markdown のリスト（またはコメント）として管理情報を追記してください。
  `画像名 | AdobeStockのURL | キャプション`

## ■ 整合性チェック
- 各タグの閉じ忘れがないか厳密に確認し、不整合があれば自動修正して出力してください。
