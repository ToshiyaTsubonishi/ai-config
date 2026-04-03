"use strict";

const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const { svgToDataUri } = require("./pptxgenjs_helpers/svg");
const {
  warnIfSlideHasOverlaps,
  warnIfSlideElementsOutOfBounds,
} = require("./pptxgenjs_helpers/layout");
const { imageSizingContain } = require("./pptxgenjs_helpers/image");
const SHAPE = new pptxgen().ShapeType;

const OUT = path.join(__dirname, "deck.pptx");

const COLORS = {
  blue: "113B74",
  blueBright: "268BE0",
  blueSoft: "EAF4FF",
  blueInk: "13233A",
  blueLine: "D8E4F1",
  red: "EA4335",
  white: "FFFFFF",
  paper: "F7FAFD",
  panel: "FFFFFF",
  panelSoft: "F7FAFD",
  gray: "5B6B82",
  graySoft: "EEF3F8",
  grayLine: "D7E1EE",
  grayInk: "40546D",
  green: "34A853",
  amber: "FBBC05",
};

const FONTS = {
  title: "Arial",
  body: "Arial",
  mono: "Courier New",
};

function assetPath(name) {
  return path.join(__dirname, "assets", name);
}

function svgAsset(name) {
  return svgToDataUri(fs.readFileSync(assetPath(name), "utf8"));
}

function addBrandMark(slide) {
  slide.addText(
    [
      { text: "SBI", options: { bold: true, color: COLORS.blueBright } },
      { text: " GROUP", options: { color: "7A7A7A" } },
    ],
    {
      x: 11.05,
      y: 0.42,
      w: 1.8,
      h: 0.32,
      fontFace: FONTS.title,
      fontSize: 21,
      align: "right",
      margin: 0,
    }
  );
}

function addChrome(slide, title, headerRight = "ai-config / April 2026") {
  slide.background = { color: COLORS.white };
  slide.addShape(SHAPE.rect, {
    x: 0.56,
    y: 0.46,
    w: 0.08,
    h: 0.58,
    line: { color: COLORS.red, transparency: 100 },
    fill: { color: COLORS.red },
  });
  slide.addText(title, {
    x: 0.78,
    y: 0.42,
    w: 8.95,
    h: 0.5,
    fontFace: FONTS.title,
    fontSize: 24,
    bold: true,
    color: "111111",
    margin: 0,
  });
  addBrandMark(slide);
  slide.addShape(SHAPE.rect, {
    x: 0.72,
    y: 1.12,
    w: 12.03,
    h: 0.34,
    line: { color: COLORS.graySoft, transparency: 100 },
    fill: { color: COLORS.graySoft },
  });
  slide.addText("会社名：SBIアートオークション / 氏名：坪西 俊哉", {
    x: 0.82,
    y: 1.17,
    w: 5.8,
    h: 0.16,
    fontFace: FONTS.body,
    fontSize: 12,
    bold: true,
    color: "222222",
    margin: 0,
  });
  slide.addText(headerRight, {
    x: 7.6,
    y: 1.17,
    w: 5.02,
    h: 0.16,
    fontFace: FONTS.body,
    fontSize: 11.5,
    bold: true,
    color: "222222",
    align: "right",
    margin: 0,
  });
  slide.addText("Copyright © 2026 SBI Holdings Inc. All Rights Reserved", {
    x: 0.18,
    y: 7.11,
    w: 5.2,
    h: 0.12,
    fontFace: FONTS.body,
    fontSize: 6.8,
    color: "666666",
    margin: 0,
  });
}

function addChip(slide, label, x, y, w) {
  slide.addShape(SHAPE.roundRect, {
    x,
    y,
    w,
    h: 0.34,
    rectRadius: 0.08,
    line: { color: COLORS.blue, transparency: 100 },
    fill: { color: COLORS.blue },
  });
  slide.addText(label, {
    x: x + 0.12,
    y: y + 0.055,
    w: w - 0.24,
    h: 0.2,
    fontFace: FONTS.body,
    fontSize: 13.5,
    bold: true,
    color: COLORS.white,
    align: "center",
    margin: 0,
  });
}

function addPanel(slide, options) {
  const {
    x,
    y,
    w,
    h,
    chip,
    chipW,
    title,
    body,
    bodyFontSize = 13.5,
    titleFontSize = 18,
    fill = COLORS.panel,
  } = options;
  slide.addShape(SHAPE.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.08,
    line: { color: COLORS.grayLine, width: 1.2 },
    fill: { color: fill },
  });
  if (chip) {
    addChip(slide, chip, x + 0.12, y - 0.13, chipW || Math.min(2.4, w - 0.24));
  }
  if (title) {
    slide.addText(title, {
      x: x + 0.2,
      y: y + 0.16,
      w: w - 0.4,
      h: 0.46,
      fontFace: FONTS.body,
      fontSize: titleFontSize,
      bold: true,
      color: COLORS.blueInk,
      margin: 0,
      valign: "mid",
    });
  }
  if (body) {
    slide.addText(body, {
      x: x + 0.2,
      y: y + 0.72,
      w: w - 0.4,
      h: h - 0.9,
      fontFace: FONTS.body,
      fontSize: bodyFontSize,
      color: COLORS.grayInk,
      margin: 0,
      valign: "top",
    });
  }
}

function addCard(slide, x, y, w, h, eyebrow, title, body, accent = COLORS.blue) {
  slide.addShape(SHAPE.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.08,
    line: { color: COLORS.grayLine, width: 1.1 },
    fill: { color: COLORS.white },
  });
  slide.addShape(SHAPE.roundRect, {
    x: x + 0.16,
    y: y + 0.16,
    w: w - 0.32,
    h: 0.25,
    rectRadius: 0.08,
    line: { color: accent, transparency: 100 },
    fill: { color: accent },
  });
  slide.addText(eyebrow, {
    x: x + 0.26,
    y: y + 0.2,
    w: w - 0.52,
    h: 0.16,
    fontFace: FONTS.body,
    fontSize: 11.5,
    color: COLORS.white,
    bold: true,
    margin: 0,
  });
  slide.addText(title, {
    x: x + 0.2,
    y: y + 0.56,
    w: w - 0.4,
    h: 0.42,
    fontFace: FONTS.body,
    fontSize: 17,
    bold: true,
    color: COLORS.blueInk,
    margin: 0,
  });
  slide.addText(body, {
    x: x + 0.2,
    y: y + 1.03,
    w: w - 0.4,
    h: h - 1.2,
    fontFace: FONTS.body,
    fontSize: 13,
    color: COLORS.grayInk,
    margin: 0,
    valign: "top",
  });
}

function addAsset(slide, name, x, y, w, h) {
  const pathToAsset = assetPath(name);
  const placement = imageSizingContain(pathToAsset, x, y, w, h);
  slide.addImage({
    data: svgAsset(name),
    x: placement.x,
    y: placement.y,
    w: placement.w,
    h: placement.h,
  });
}

function finalizeSlide(slide, pptx) {
  if (process.env.PPTX_STRICT_LAYOUT === "1") {
    warnIfSlideHasOverlaps(slide, pptx, { muteContainment: true });
    warnIfSlideElementsOutOfBounds(slide, pptx);
  }
}

function buildSlides(pptx) {
  let slide;

  slide = pptx.addSlide();
  addChrome(slide, "2026年4月 AIアンバサダー報告会_成果報告", "（2026年4月報告時点） ai-config中心の成果");
  addPanel(
    slide,
    {
      x: 0.55,
      y: 1.82,
      w: 6.05,
      h: 3.5,
      chip: "① 課題と背景",
      chipW: 2.3,
      title: "AI活用で先に詰まるのは「何を使うべきか」",
      body:
        "Skill / MCP が増えるほど、候補の見極めが難しくなる。\n不要な候補が混ざると説明コストとコンテキスト負荷が増え、環境差分があると再現性も落ちる。\nそこで今月は、道具選びと計画づくりの部分を ai-config として明確に整理した。",
    }
  );
  addPanel(
    slide,
    {
      x: 6.82,
      y: 1.82,
      w: 5.98,
      h: 3.5,
      chip: "② 成果",
      chipW: 1.9,
      title: "control plane として ai-config を整理",
      body:
        "selector-serving を read-only の公開面として整備。\nOpen WebUI + MCPO の接続テンプレートを repo に追加。\nローカルでは search と readiness 応答まで確認し、説明と実演の両方に耐える材料をそろえた。",
    }
  );
  addPanel(
    slide,
    {
      x: 0.55,
      y: 5.72,
      w: 12.25,
      h: 1.3,
      chip: "③ 今後の展望",
      chipW: 2.3,
      title: "Open WebUI デモを軸に、候補精度と plan 活用を次フェーズへつなぐ",
      body:
        "今回は CLI だけでなく、UI から MCP として使えることを見せる。次は候補精度、approved plan 活用、業務ドメイン向け Skill / MCP の拡張へ進める。",
      bodyFontSize: 13,
      titleFontSize: 15.5,
    }
  );
  finalizeSlide(slide, pptx);

  slide = pptx.addSlide();
  addChrome(slide, "1. 今月の要約", "selector-serving / Open WebUI / control plane");
  addCard(
    slide,
    0.75,
    1.95,
    3.92,
    4.3,
    "1 / selector-serving",
    "read-only の公開面を整理",
    "Cloud Run に載せる標準 surface を `ai-config-selector-serving` に固定。\n`/mcp`、`/healthz`、`/readyz` を明示し、runtime では index build を行わない前提に整理した。",
    COLORS.blue
  );
  addCard(
    slide,
    4.73,
    1.95,
    3.92,
    4.3,
    "2 / Open WebUI",
    "MCPO 経由の接続テンプレートを追加",
    "Open WebUI から ai-config を tool server として扱えるように、selector / MCPO / Open WebUI それぞれの Cloud Run テンプレートと secret sample を repo に持たせた。",
    COLORS.blueBright
  );
  addCard(
    slide,
    8.71,
    1.95,
    3.92,
    4.3,
    "3 / architecture",
    "control plane として説明可能にした",
    "ai-config の主役を selector / planner / boundary に置き、execution runtime は dispatch 側に分ける構成を明文化。エンジニア相手にも筋の通った説明がしやすくなった。",
    COLORS.green
  );
  addPanel(slide, {
    x: 0.75,
    y: 6.47,
    w: 11.88,
    h: 0.52,
    title: "一言でいうと: ai-config は「AI の実行エンジン」ではなく「AI の道具選びと実行前整理を担う基盤」",
    body: "",
    titleFontSize: 16,
    fill: COLORS.blueSoft,
  });
  finalizeSlide(slide, pptx);

  slide = pptx.addSlide();
  addChrome(slide, "2. 今回の見せ方", "実画面・補助図・ライブデモ");
  addCard(slide, 0.85, 2.0, 3.75, 4.25, "A", "実画面", "Open WebUI や selector の動く様子は理解を早める。ただし UI の派手さを見せたいのではなく、接続済みであることを伝えるための材料として使う。");
  addCard(slide, 4.79, 2.0, 3.75, 4.25, "B", "補助図", "責務分離や MCP 接続は静止画のほうが説明しやすい。デモが不安定でも、構造の話は補助図だけで成立するようにしておく。 ", COLORS.blueBright);
  addCard(slide, 8.73, 2.0, 3.75, 4.25, "C", "ライブデモ", "Open WebUI から『使うべき Skill / MCP を探して』と依頼し、search → detail → downstream MCP 確認の順に見せる。成功時は説得力、失敗時は Slide 12 に切り替える。", COLORS.green);
  addPanel(slide, {
    x: 0.85,
    y: 6.5,
    w: 11.63,
    h: 0.52,
    title: "今日見せたいのは AI の万能感ではなく、『必要な道具を必要なタイミングで探して使える状態』",
    body: "",
    titleFontSize: 16,
    fill: COLORS.blueSoft,
  });
  finalizeSlide(slide, pptx);

  slide = pptx.addSlide();
  addChrome(slide, "3. 活動の背景と課題", "候補選定 / context / environment / ownership");
  addCard(slide, 0.82, 1.92, 5.8, 2.0, "課題 1", "候補が増える", "Skill / MCP が増えるほど、正しいものを選ぶ難度が上がる。全部を頭に入れておく前提では運用が重くなる。");
  addCard(slide, 6.7, 1.92, 5.8, 2.0, "課題 2", "コンテキストが膨らむ", "不要な候補を事前投入すると、使わない情報まで説明し続けることになる。選定品質にも悪影響が出やすい。 ", COLORS.blueBright);
  addCard(slide, 0.82, 4.18, 5.8, 2.0, "課題 3", "環境差分が出る", "CLI ごとの差、MCP の登録差、運用環境の制約が混ざると、同じ手順でも再現しにくくなる。", COLORS.green);
  addCard(slide, 6.7, 4.18, 5.8, 2.0, "課題 4", "責任分界が曖昧になる", "選定、計画、実行が混ざると、どこで何を保証しているのか説明しにくい。結果としてレビューや引き継ぎのコストも上がる。", COLORS.red);
  finalizeSlide(slide, pptx);

  slide = pptx.addSlide();
  addChrome(slide, "4. ゴールとアプローチ", "selector / planner / execution boundary");
  addPanel(slide, {
    x: 0.8,
    y: 1.92,
    w: 5.28,
    h: 4.9,
    chip: "To-Be",
    chipW: 1.2,
    title: "ai-config を execution runtime ではなく control plane に置く",
    body:
      "扱いたい中心は 3 つ。\n\n1. Skill / MCP の catalog と index\n2. selector による候補検索と詳細確認\n3. approved plan という planning artifact\n\n実行の DAG、retry、parallelism、context handoff は dispatch runtime に渡し、境界で契約を固定する。",
    bodyFontSize: 13.2,
  });
  addCard(slide, 6.33, 1.92, 2.06, 2.2, "Principle", "Selector First", "Agent はまず selector で候補を探す。", COLORS.blue);
  addCard(slide, 8.62, 1.92, 2.06, 2.2, "Principle", "Plan As Artifact", "複雑タスクでは approved plan を先に作る。", COLORS.blueBright);
  addCard(slide, 10.91, 1.92, 1.87, 2.2, "Principle", "Boundary", "execution runtime とは stable contract でつなぐ。", COLORS.green);
  addPanel(slide, {
    x: 6.33,
    y: 4.45,
    w: 6.45,
    h: 2.37,
    chip: "設計上の狙い",
    chipW: 1.9,
    title: "説明しやすく、切り離しやすく、運用しやすい構成にする",
    body:
      "派手な runtime 機能を同じ repo に抱え込まず、ai-config は selection quality / planning quality / provenance を担う。\nこれにより、Open WebUI デモでも『何を解決している repo なのか』を短時間で説明できる。",
    bodyFontSize: 13.2,
    titleFontSize: 16.5,
  });
  finalizeSlide(slide, pptx);

  slide = pptx.addSlide();
  addChrome(slide, "5. 役割分離の全体像", "Agent → selector → ApprovedPlan → dispatch");
  addAsset(slide, "architecture-overview.svg", 0.76, 1.72, 12.0, 5.0);
  addPanel(slide, {
    x: 0.76,
    y: 6.18,
    w: 12.0,
    h: 0.8,
    title: "本 repo の主役は selector / planner / boundary。 execution runtime の詳細を中央に置かないことで、説明と保守の軸を保ちやすい。",
    body: "",
    titleFontSize: 15.5,
    fill: COLORS.blueSoft,
  });
  finalizeSlide(slide, pptx);

  slide = pptx.addSlide();
  addChrome(slide, "6. ai-config の中身", "catalog / index / selector / planner artifact / boundary");
  addCard(slide, 0.78, 1.9, 2.32, 2.2, "Layer 1", "Catalog / Index", "Skill / MCP source を catalog 化し、index を build して candidate retrieval の土台をつくる。", COLORS.blue);
  addCard(slide, 3.28, 1.9, 2.32, 2.2, "Layer 2", "Selector", "search_tools、get_tool_detail、downstream MCP bridge で『何を使うか』を返す。", COLORS.blueBright);
  addCard(slide, 5.78, 1.9, 2.32, 2.2, "Layer 3", "Planner Artifact", "必要時だけ ApprovedPlan を作り、validation と controlled replan を扱う。", COLORS.green);
  addCard(slide, 8.28, 1.9, 2.32, 2.2, "Layer 4", "Execution Boundary", "plan を ApprovedPlanExecutionRequest にして dispatch へ渡す。", COLORS.red);
  addCard(slide, 10.78, 1.9, 2.32, 2.2, "Layer 5", "Read-only Serving", "selector-serving は index を読むだけの runtime として公開する。", COLORS.blue);
  addPanel(slide, {
    x: 0.78,
    y: 4.58,
    w: 12.02,
    h: 2.18,
    chip: "エンジニア向けに伝わりやすい一言",
    chipW: 2.9,
    title: "ai-config は capability broker であり、単なるツール置き場ではない",
    body:
      "価値の中心は runtime の派手さではなく、selection quality と planning quality。\nrepo が正本として持つのは catalog / retrieval / policy / plan artifact / runtime validation / provenance であり、execution の詳細は boundary の外で扱う。",
    bodyFontSize: 14,
    titleFontSize: 17,
  });
  finalizeSlide(slide, pptx);

  slide = pptx.addSlide();
  addChrome(slide, "7. Open WebUI 連携の構成", "Open WebUI → MCPO → ai-config-selector-serving");
  addAsset(slide, "openwebui-connection.svg", 0.72, 1.72, 8.25, 4.95);
  addPanel(slide, {
    x: 9.2,
    y: 1.92,
    w: 3.48,
    h: 4.72,
    chip: "ポイント",
    chipW: 1.35,
    title: "なぜ Open WebUI デモが効くのか",
    body:
      "1. CLI だけでなく、既存 UI から使える形を見せられる\n\n2. ai-config を『ただの設定 repo』ではなく、MCP として触れる surface にできていることが伝わる\n\n3. 社内の利用イメージを非エンジニアにも共有しやすい",
    bodyFontSize: 13.2,
    titleFontSize: 16.5,
  });
  finalizeSlide(slide, pptx);

  slide = pptx.addSlide();
  addChrome(slide, "8. デモで見せるポイント", "search → detail → downstream MCP");
  addCard(slide, 0.78, 1.88, 3.85, 1.48, "Step 1", "候補探索", "『この依頼に使うべき Skill / MCP を探して』と依頼し、search_tools 相当の動きを起点にする。", COLORS.blue);
  addCard(slide, 4.74, 1.88, 3.85, 1.48, "Step 2", "詳細確認", "候補のうち適切なものを選び、get_tool_detail で実行手順や注意点を確認する。", COLORS.blueBright);
  addCard(slide, 8.7, 1.88, 3.85, 1.48, "Step 3", "接続確認", "必要なら downstream MCP の tool list まで見せ、検索だけでなく bridge も動くことを示す。", COLORS.green);
  addPanel(slide, {
    x: 0.78,
    y: 3.68,
    w: 4.02,
    h: 2.95,
    chip: "ライブプロンプト",
    chipW: 1.75,
    title: "Open WebUI で最初に打つ文",
    body:
      "この依頼に使うべき Skill / MCP を先に探して、理由つきで候補を出してください。\n候補のうち一番適切なものの詳細を確認してください。\n利用可能な downstream MCP の tool list も確認してください。",
    bodyFontSize: 13.2,
    titleFontSize: 16.5,
  });
  addAsset(slide, "selector-search.svg", 5.04, 3.68, 7.5, 3.2);
  finalizeSlide(slide, pptx);

  slide = pptx.addSlide();
  addChrome(slide, "9. 成果サマリー", "公開面 / 接続 / 責務分離 / 検証");
  addCard(slide, 0.8, 1.95, 5.8, 2.02, "成果 1", "read-only selector-serving を整理", "standard HTTP surface を `ai-config-selector-serving` に固定し、`/mcp`、`/healthz`、`/readyz` を明示。runtime で index build しない前提も整理した。", COLORS.blue);
  addCard(slide, 6.72, 1.95, 5.8, 2.02, "成果 2", "Open WebUI + MCPO の接続テンプレートを repo 化", "selector / MCPO / Open WebUI それぞれの Cloud Run テンプレートと secret sample JSON を追加し、接続手順の再現性を上げた。", COLORS.blueBright);
  addCard(slide, 0.8, 4.25, 5.8, 2.02, "成果 3", "plan と execution の責務分離を説明可能に", "ai-config を selector / planner の control plane として扱い、dispatch runtime とは stable boundary でつなぐ整理を明文化した。", COLORS.green);
  addCard(slide, 6.72, 4.25, 5.8, 2.02, "成果 4", "ローカル検証と発表用 evidence を確保", "search 結果、schema 確認、selector-serving readiness を押さえ、ライブデモが失敗しても説明が続けられる材料をそろえた。", COLORS.red);
  finalizeSlide(slide, pptx);

  slide = pptx.addSlide();
  addChrome(slide, "10. エンジニア向けの価値", "selection quality / ownership / operations");
  addCard(slide, 0.82, 1.95, 5.76, 2.1, "Value 1", "Selection Quality", "全候補を最初から抱え込まず、必要なときだけ候補を返すので、選定ミスや説明コストを抑えやすい。", COLORS.blue);
  addCard(slide, 6.72, 1.95, 5.76, 2.1, "Value 2", "責任分界", "selector / planner / execution boundary を切ることで、どこが何を保証しているかが明確になる。", COLORS.blueBright);
  addCard(slide, 0.82, 4.34, 5.76, 2.1, "Value 3", "Provenance / Ownership", "vendor source、index、template の正本管理を repo に残し、運用上の provenance を保ちやすくしている。", COLORS.green);
  addCard(slide, 6.72, 4.34, 5.76, 2.1, "Value 4", "運用しやすさ", "selector-serving を read-only surface として公開できるので、実運用の説明と review に耐えやすい。", COLORS.red);
  finalizeSlide(slide, pptx);

  slide = pptx.addSlide();
  addChrome(slide, "11. デモ補強と検証証跡", "healthz / readyz / templates / local evidence");
  addAsset(slide, "validation-evidence.svg", 0.72, 1.72, 8.1, 5.02);
  addPanel(slide, {
    x: 9.0,
    y: 1.92,
    w: 3.68,
    h: 4.8,
    chip: "Fallback",
    chipW: 1.4,
    title: "ライブ失敗時の話し方",
    body:
      "今日は UI の派手さを見せたいのではなく、必要な道具を必要なタイミングで探して使える構成を見せたい。\n\nライブ動作が難しい場合でも、公開面・テンプレート・ローカル readiness の 3 点で実装の進捗は示せる。",
    bodyFontSize: 13.3,
    titleFontSize: 16.5,
  });
  finalizeSlide(slide, pptx);

  slide = pptx.addSlide();
  addChrome(slide, "12. 今後の展望", "候補精度 / approved plan / domain skills");
  addPanel(slide, {
    x: 0.82,
    y: 1.95,
    w: 5.9,
    h: 4.55,
    chip: "短期 / Phase 2",
    chipW: 1.95,
    title: "Open WebUI デモを安定運用に寄せる",
    body:
      "・候補探索 → detail → downstream MCP の見せ方を固定する\n・実画面の差し替えやスクリーンショットを追加し、補助図依存を減らす\n・selector-serving と template 群の説明を、社内共有しやすい粒度まで整理する",
    bodyFontSize: 14,
  });
  addPanel(slide, {
    x: 6.9,
    y: 1.95,
    w: 5.9,
    h: 4.55,
    chip: "中長期 / Phase 3",
    chipW: 2.2,
    title: "業務ドメインに近い Skill / MCP を増やす",
    body:
      "・候補精度の改善と approved plan 活用を進める\n・社内知識や業務フローを Skill / MCP として積み増す\n・定期的な棚卸しを行い、古い候補や曖昧な運用を減らす",
    bodyFontSize: 14,
  });
  addPanel(slide, {
    x: 0.82,
    y: 6.72,
    w: 11.98,
    h: 0.36,
    title: "目指す姿: ai-config を『育て続けられる control plane』として運用に載せる",
    body: "",
    titleFontSize: 15.5,
    fill: COLORS.blueSoft,
  });
  finalizeSlide(slide, pptx);
}

async function main() {
  const pptx = new pptxgen();
  pptx.layout = "LAYOUT_WIDE";
  pptx.author = "OpenAI Codex";
  pptx.company = "SBIアートオークション";
  pptx.subject = "2026年4月 AIアンバサダー報告会 成果報告";
  pptx.title = "2026年4月 AIアンバサダー報告会_成果報告";
  pptx.lang = "ja-JP";
  pptx.theme = {
    headFontFace: FONTS.title,
    bodyFontFace: FONTS.body,
    lang: "ja-JP",
  };

  buildSlides(pptx);

  await pptx.writeFile({ fileName: OUT });
  console.log(`Wrote ${OUT}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
