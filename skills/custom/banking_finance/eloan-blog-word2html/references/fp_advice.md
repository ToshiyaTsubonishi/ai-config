# FPアドバイス HTML 変換ルール (E-LOAN テンプレート準拠)

## ■ 基本仕様
- HTMLファイルの文字コードは **UTF-8**、改行コードは **LF** とします。
- 段落先頭の全角スペース（`　`）は削除してください。
-  `<b>` （太字強調）は重要です。絶対に省略せず、すべて `<strong>` でマークアップしてください。

## ■ HTML 全体構造
`assets/fp_advice_template.html` をベースに使用してください。
抽出された記事コンテンツは、テンプレート内の `<!-- CONTENT_START -->` と `<!-- CONTENT_END -->` の間に挿入します。
ヘッダー、フッター、CSSリンク、および body クラス (`fp`) はテンプレートのものを維持してください。

## ■ Q&A セクション
記事冒頭の Q と A は以下の形式でマークアップしてください。
```html
<div class="detContInner3 fpQaCont">
    <dl class="clearfix mgbt10">
        <dd class="fpQ">Qテキスト（最後に「（会社員　50代）」などの属性があれば含める）</dd>
        <dd class="fpA">Aテキスト</dd>
    </dl>
</div>
```

## ■ 見出し (H3)
見出しは `<h3>` を使用し、以下のラッパーを使用してください。
```html
<div class="detContSubTitWap4 mgbt10">
    <div class="subTitInner">
        <h3><strong>見出しテキスト</strong></h3>
    </div>
</div>
```

## ■ 段落
- 原則として `<p class="indentTab2 mgbt10">...</p>` を使用してください。

## ■ テーブル変換
- `<table>` は必ず以下の構造でラップ・構成してください。
  ```html
  <div class="column">
      <p><strong>条件）</strong> 借入額：200万円 ...</p>
  </div>
  <div class="scrollTable">
      <table class="table_tab" width="100%">
          <caption>表タイトル</caption>
          <thead>...</thead>
          <tbody>...</tbody>
      </table>
  </div>
  ```
- 金額等の右寄せが必要なセルには `class="right"`、中央寄せには `class="center"` を付与してください。
- 補足説明には `<p class="note">...</p>` を使用してください。

## ■ 参考リンク
記事末尾の参考リンクは以下の構造にしてください。
```html
<div class="detContInner3 mgbt10">
    <p>【参考リンク】<br />
    <ul class="iconArrowL">
        <li><a href="...">リンクテキスト</a></li>
    </ul>
    </p>
</div>
```

## ■ 禁止事項
- `span`, `font`, `em`, `blockquote` などの使用は禁止。
- 原則としてテンプレート構成要素以外の `div` は禁止ですが、上記のラッパーとしての使用は許可されます。
