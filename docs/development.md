# ai-config 開発者ガイド

## 開発環境セットアップ

```bash
git clone https://github.com/ToshiyaTsubonishi/ai-config.git
cd ai-config
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,semantic]"
```

## プロジェクト構造

```
ai-config/
├── src/ai_config/           # メインパッケージ
│   ├── mcp_server/          # MCP サーバー (server.py, tools.py)
│   ├── registry/            # パーサー・インデックスビルダー
│   ├── retriever/           # ハイブリッド検索 (hybrid_search.py)
│   ├── orchestrator/        # LangGraph オーケストレーション
│   ├── executor/            # ツール実行エンジン
│   │   └── adapters/       # CLI アダプター (codex, gemini, antigravity)
│   ├── dispatch/            # マルチエージェント・ディスパッチ
│   ├── build_index.py       # インデックス構築 CLI
│   └── source_manager.py    # 外部ソース管理 CLI
├── tests/                   # テストスイート
├── config/                  # 設定ファイル
├── workflows/               # ワークフロー定義 (YAML)
├── skills/                  # スキルコレクション
└── pyproject.toml           # プロジェクト設定
```

## テスト

### テスト実行

```bash
# 全テスト実行
.venv/bin/python -m pytest tests/ -v

# 特定モジュールのテスト
.venv/bin/python -m pytest tests/test_dispatch_graph.py -v

# カバレッジ計測
.venv/bin/python -m pytest tests/ --cov=ai_config --cov-report=term-missing
```

### テストの構成

| テストファイル | 対象モジュール | テスト数 |
|---|---|---|
| `test_dispatch_graph.py` | dispatch/graph, evaluator | 12 |
| `test_dispatch_planner.py` | dispatch/planner | 10 |
| `test_dispatch_workflow.py` | dispatch/workflow, dispatcher | 13 |
| `test_dispatch_approved_plan.py` | dispatch approved-plan execution | 1 |
| `test_orchestrator_repair_loop.py` | orchestrator (統合) | 2 |
| `test_orchestrator_router.py` | orchestrator/router | 3 |
| `test_orchestrator_plan_artifacts.py` | orchestrator plan schema / planner / validator | 3 |
| `test_executor_adapters.py` | executor | 4 |
| `test_mcp_server_tools.py` | mcp_server/tools | 5 |
| `test_cli_smoke.py` | CLI 統合 | 2 |
| `test_index_builder_contract.py` | registry/index_builder | 1 |
| `test_retriever_rrf.py` | retriever/hybrid_search | 1 |
| その他 | registry, source_manager | 18 |

### テストのポイント

- **LLM 依存テスト**: `_get_llm()` を `lambda: None` にモンキーパッチしてフォールバック経路をテスト
- **CLI テスト**: `subprocess.run` をモックして外部コマンド呼び出しを回避
- **統合テスト**: `test_orchestrator_repair_loop.py` は `npx` が必要（なければ skip）

## 新しいスキルの追加

### 方法 1: ローカルスキル

`skills/shared/<skill-name>/SKILL.md` を作成:

```markdown
---
name: my-skill
description: スキルの説明
---
# My Skill

スキルの詳細な指示...
```

### 方法 2: カスタムスキル（ドメイン分割）

```
skills/custom/<domain>/<skill-name>/SKILL.md
```

例:
```
skills/custom/human_resources/onboarding-guide/SKILL.md
skills/custom/technology/api-design/SKILL.md
```

### 方法 3: 外部スキルリポジトリ

`config/sources.yaml` に追加:

```yaml
sources:
  my-skills:
    type: skill
    url: https://github.com/user/skills.git
    path: skills/external/my-skills
    branch: main
```

## 新しいワークフローの追加

`workflows/<name>.yaml` を作成します。テンプレート:

```yaml
name: my-workflow
description: "ワークフローの説明"
variables:
  custom_var: "default_value"
steps:
  - step_id: step-1
    description: "ステップの説明"
    agent: gemini              # gemini | codex | antigravity
    prompt_template: |
      {user_prompt}
      カスタム変数: {custom_var}
    depends_on: []             # 依存ステップの ID リスト
    timeout_seconds: 300
```

## 新しいアダプターの追加

1. `src/ai_config/executor/adapters/` にアダプタークラスを作成
2. `BaseAdapter` を継承
3. `command()`, `list_tools()`, `call()` を実装
4. `executor/__init__.py` と `mcp_wrapper.py` に登録

## コーディング規約

- **型注釈**: すべての関数に型注釈を付ける
- **docstring**: 公開関数・クラスには必ず docstring を記述
- **`from __future__ import annotations`**: 全モジュールで使用
- **ロギング**: `logging.getLogger(__name__)` を使用
- **エラーハンドリング**: `ExecutorError` / `ExecutorErrorCode` を活用
- **テストの命名**: `test_<対象>_<条件>` 形式

## 技術スタック

| ライブラリ | 用途 | バージョン |
|---|---|---|
| LangGraph | ステートグラフ・オーケストレーション | ≥ 0.3 |
| langchain-google-genai | Gemini LLM 呼び出し | ≥ 2.0 |
| numpy | ベクトル演算 | ≥ 1.26 |
| rank-bm25 | BM25 検索 | ≥ 0.2 |
| pyyaml | YAML パース | ≥ 6.0 |
| python-frontmatter | SKILL.md パース | ≥ 1.1 |
| pydantic | スキーマバリデーション | ≥ 2.8 |
| mcp | MCP サーバー SDK | ≥ 1.0 |
| sentence-transformers | 多言語エンベディング (オプション) | ≥ 3.0 |
| faiss-cpu | ベクトルインデックス (オプション) | ≥ 1.9 |
