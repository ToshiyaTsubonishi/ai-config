# ai-config

AI ツール（Codex / Antigravity / Gemini CLI）の MCP とスキルを動的に検索・選択する MCP サーバー。

各 AI ツールに `ai-config-selector` を 1 つ登録するだけで、905+ のスキルと MCP サーバーを自然言語で検索して利用できます。

## アーキテクチャ

```
AI Tool (Codex / Antigravity / Gemini CLI)
    │
    └── ai-config-selector (MCP Server)
            │
            ├── search_tools(query)     → ツール検索
            ├── get_tool_detail(id)     → 詳細取得
            ├── list_categories()       → カテゴリ一覧
            └── get_tool_count()        → 総数
            │
            └── .index/ (ハイブリッド検索エンジン)
                    ├── records.json     (905+ ツールレコード)
                    ├── faiss.bin        (ベクトルインデックス)
                    ├── bm25.pkl         (BM25 インデックス)
                    └── keyword_index.json (キーワード完全一致)
```

## セットアップ

```bash
git clone https://github.com/ToshiyaTsubonishi/ai-config-sync.git
cd ai-config-sync
bash scripts/setup.sh
```

## 各 AI ツールに登録

```bash
# 全ツールに一括登録
bash scripts/register.sh

# 個別登録
bash scripts/register.sh antigravity
bash scripts/register.sh gemini_cli
bash scripts/register.sh codex
```

## CLI ツール

```bash
# インデックス構築
ai-config-index --repo-root .

# インデックス構築 (watch モード)
ai-config-index --repo-root . --watch

# MCP サーバー起動 (通常は AI ツールが自動起動)
ai-config-mcp-server --repo-root .

# オーケストレーター (検索のみ)
ai-config-agent "ESLint の設定を確認したい" --search-only

# オーケストレーター (フル実行)
ai-config-agent "codex で実行して" --top-k 8 --max-retries 2
```

## ディレクトリ構成

```
ai-config-sync/
├── src/ai_config/
│   ├── mcp_server/      # 動的選択 MCP サーバー
│   ├── registry/         # ツールパーサー・インデックスビルダー
│   ├── retriever/        # ハイブリッド検索 (BM25 + ベクトル + RRF)
│   ├── orchestrator/     # LangGraph オーケストレーション
│   ├── executor/         # ツール実行エンジン
│   ├── build_index.py    # インデックス構築 CLI
│   └── source_manager.py # 外部ソース管理
├── skills/               # スキルコレクション (510+)
├── config/
│   ├── master/ai-sync.yaml  # ツールカタログ設定
│   └── sources.yaml         # 外部スキルソース定義
├── .index/               # 構築済みインデックス
├── scripts/
│   ├── setup.sh          # セットアップ
│   └── register.sh       # MCP 登録
└── tests/                # テスト
```

## ツールカタログ

`config/master/ai-sync.yaml` にマネージド MCP サーバー定義とスキルセットを記述します。
これらは `ai-config-index` でインデックス化され、`ai-config-selector` MCP を通じて動的に検索されます。

## LLM 設定

オーケストレーターの LLM モデルは環境変数 `GEMINI_MODEL` で指定します（デフォルト: `gemini-flash-latest`）。

## 環境変数

`.env.example` を `.env` にコピーして設定してください:

- `GOOGLE_API_KEY` — オーケストレーター用
- `GITHUB_PERSONAL_ACCESS_TOKEN` — GitHub MCP 用
- その他 MCP サーバー固有のキー

## 注意

- `.env` はコミットしないでください（`.gitignore` 対象）
- Python 3.11+ が必要です
