# Lessons Learned

## 2026-03-03: ai-config-dispatch とai-config-selector の活用

### ミス 1: ai-config-dispatch を使用しなかった

- **状況**: ユーザーが `ai-config-dispatch "..."` 形式でプロンプトを送信した
- **期待動作**: `ai-config-dispatch` CLI を実行して Codex/Gemini CLI に作業を分散する
- **実際の動作**: dispatch を無視して直接作業してしまった
- **ルール**: プロンプトが `ai-config-dispatch` で始まる場合、必ず dispatch システムを通じてマルチエージェントで作業する。自分（Antigravity）はオーケストレーターとして振る舞い、計画・実行・検証を監督する。

### ミス 2: ai-config-selector で検索しなかった

- **状況**: ai-config-selector の MCP ツール (`search_tools`) が利用可能だった
- **期待動作**: タスク開始時に `search_tools` で関連スキル / MCP を検索する
- **実際の動作**: 一切検索せず直接作業した
- **ルール**: タスク開始時に必ず `search_tools` で関連ツールを検索する。結果がなくても検索すること自体が正しい動作。見つかったスキルがあれば活用する。

### ミス 3: Gemini API の response.content が list を返すケースを未考慮

- **状況**: `response.content` が `str` であることを前提にしていたが、Gemini API は multi-part content の場合 `list` を返す
- **影響**: `'list' object has no attribute 'strip'` で LLM プランニングが毎回フォールバックに落ちていた
- **修正**: `_extract_text()` ヘルパー関数を追加。`list` の場合は各パーツの `.text` を結合する
- **ルール**: LLM レスポンスの `content` フィールドは常に `str | list` の両方をハンドルする

## 2026-03-11: 読み取り専用の複数観点検証でも dispatch を使う

### ミス 4: repo inspection / validation を direct 実行してしまった

- **状況**: Windows setup / MCP registration / downstream MCP / instruction sync のように複数の観点を横断する読み取り専用タスクを受けた
- **期待動作**: `ai-config-selector` で候補を確認したうえで、`.venv\Scripts\ai-config-dispatch.cmd` を使って検証を分担し、証拠を集約する
- **実際の動作**: 読み取り専用だから trivial と判断して direct に調査してしまった
- **ルール**: 読み取り専用でも、2つ以上の観点・サブシステムを横断する repo inspection / setup validation / MCP validation は非自明タスクとして dispatch を優先する

## 2026-03-12: 観測 API の契約は最初に固定する

### ミス 5: observability の severity と JSON 互換性を後から補強する形になった

- **状況**: vendor observability の実装計画に対して、`unmanaged_local` の doctor 扱いと `status --json` の安定 schema が後から明文化された
- **期待動作**: local state を返す観測 API では、実装前に severity と JSON contract を固定する
- **実際の動作**: 初期実装案では `extra_local` と `unmanaged_local` の扱い差、`schema_version` / `generated_at` を明示していなかった
- **ルール**: 新しい observability/status API を追加するときは、実装前に「どの状態が fail/pass か」と「JSON schema version / generation timestamp」を必ず決めてから着手する
