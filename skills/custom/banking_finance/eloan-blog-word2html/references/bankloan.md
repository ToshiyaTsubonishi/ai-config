# bankloan HTML 変換ルール

## ■ 基本仕様

- 「執筆時に参考にしたURL」以降の内容は削除してください。
- HTML ファイルの文字コードは **UTF-8**、改行コードは **LF** とします。
- 最大の見出しは **H2**、以下は H3 → H4 → H5 → H6 の順とします。
- 段落先頭にある全角スペース `　` は削除してください。
-  `<b>` （太字強調）は重要です。絶対に省略せず、すべて `<strong>` でマークアップしてください。

## ■ 全体構造
`assets/bankloan_template.html` をベースに使用してください。
抽出された記事コンテンツは、テンプレート内の `<!-- CONTENT_START -->` と `<!-- CONTENT_END -->` の間に挿入します。
ヘッダー、フッター、CSSリンク、および body クラス (`card`) / ID (`useful`) はテンプレートのものを維持してください。

## ■ 許可される HTML タグ
`strong, table, thead, tbody, tfoot, tr, th, td, ul, ol, li, p, h2, h3, h4, h5, h6, img, br, dl, dt, dd`
※ `div` や `section` はテンプレート構成要素としてのみ許可。
※ `span, em, blockquote, font` は原則禁止。

## ■ 見出し・強調
- 段落全体が太字の場合は見出し（H2, H3...）とみなします。
- 表のセルの文言がすべて太字の場合は `<th>` を使用。

## ■ リスト変換
- Word 内の箇条書きは `<ul><li>` に変換。
- 閉じタグの整合性を必ずチェック。

## ■ テーブル変換
- `<th>` や `<td>` 内での `<br>` は許可。
- `<table>` は必ず以下の構造でラップ。
  ```html
  <div class="scrollTable" data-scroll="horizontal"><div data-guide="scroll"><table class="tab">
  ```
- 終了時は `</tbody></table></div></div>` で閉じる。

## ■ FAQ (よくある質問)
- 記事末尾の Q&A は以下の形式でマークアップ。
  ```html
  <dl class="faqBox">
    <dt>質問文</dt>
    <dd>回答文</dd>
  </dl>
  ```

## ■ 画像の取り扱い
- **形式**: `<img alt="Altテキスト" src="/unified/images/articles/useful/{Issue}/{連番}.jpg">`
  - `{Issue}`: 記事番号（例：110）
  - `{連番}`: 出現順に `main`, `01`, `02`, `03` ...
- **属性**: `alt` には画像のキャプションを入れる。
- **配置**: 画像を `<p>` タグで囲まない。
- **Resumeクラス**: 画像の直後の段落には `<p class="resume">` を付与。

## ■ 画像一覧（末尾）
- HTML出力の**外（ファイルの最後）**に、以下の形式で Markdown 形式の一覧表を追記。
  `画像名 | AdobeStockのURL | キャプション`

## ■ 整合性チェック
- 開始・終了タグの整合性を厳密に検証し、自動修正して出力。
