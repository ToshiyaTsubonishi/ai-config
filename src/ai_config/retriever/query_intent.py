"""Heuristic query intent extraction for retrieval narrowing."""

from __future__ import annotations

from dataclasses import dataclass

from ai_config.registry.normalization import normalize_targets


@dataclass
class QueryIntent:
    tool_kinds: list[str]
    targets: list[str]
    capabilities: list[str]


def infer_query_intent(query: str) -> QueryIntent:
    q = query.lower()

    tool_kinds: set[str] = set()
    targets: set[str] = set()
    capabilities: set[str] = set()

    if any(token in q for token in ("mcp", "server", "設定", "config", "configuration")):
        tool_kinds.add("mcp_server")
    if any(token in q for token in ("script", "スクリプト", "ps1", "python", "bash", "shell")):
        tool_kinds.add("skill_script")
    if any(token in q for token in ("skill", "instructions", "ガイド", "ワークフロー")):
        tool_kinds.add("skill")
    if any(token in q for token in ("adapter", "cli", "実行エンジン", "toolchain")):
        tool_kinds.add("toolchain_adapter")
        capabilities.add("cli_execution")

    if any(
        token in q
        for token in (
            "fix",
            "bug",
            "test",
            "build",
            "review",
            "refactor",
            "implement",
            "debug",
            "repair",
            "patch",
            "修正",
            "バグ",
            "テスト",
            "ビルド",
            "レビュー",
            "リファクタ",
            "実装",
            "デバッグ",
            "検証",
        )
    ):
        tool_kinds.add("toolchain_adapter")
        capabilities.add("cli_execution")

    if "codex" in q:
        targets.add("codex")
    if "gemini" in q:
        targets.add("gemini")
    if "antigravity" in q:
        targets.add("antigravity")

    if any(token in q for token in ("execute", "run", "実行", "呼び出し", "invoke")):
        capabilities.add("cli_execution")

    return QueryIntent(
        tool_kinds=sorted(tool_kinds),
        targets=normalize_targets(targets),
        capabilities=sorted(capabilities),
    )
