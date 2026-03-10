"""Heuristics for ranking action-oriented software tooling above generic skills."""

from __future__ import annotations

from ai_config.retriever.hybrid_search import SearchHit

_SOFTWARE_ACTION_TOKENS = (
    "fix",
    "bug",
    "test",
    "build",
    "review",
    "refactor",
    "implement",
    "debug",
    "repair",
    "investigate",
    "analyze",
    "audit",
    "patch",
    "修正",
    "バグ",
    "テスト",
    "ビルド",
    "レビュー",
    "リファクタ",
    "実装",
    "デバッグ",
    "調査",
    "検証",
)

_VISUAL_TOKENS = ("ui", "browser", "visual", "screenshot", "playwright", "画面", "ブラウザ")


def is_action_oriented_software_query(query: str) -> bool:
    q = query.lower()
    return any(token in q for token in _SOFTWARE_ACTION_TOKENS)


def boost_hits(query: str, hits: list[SearchHit]) -> list[SearchHit]:
    if not hits or not is_action_oriented_software_query(query):
        return hits

    q = query.lower()

    def _score(hit: SearchHit) -> tuple[float, float, float]:
        record = hit.record
        bonus = 0.0
        if record.tool_kind == "toolchain_adapter":
            bonus += 1.0
        if record.id == "toolchain:codex":
            bonus += 0.45
        elif record.id == "toolchain:gemini_cli":
            bonus += 0.35
        elif record.id == "toolchain:antigravity":
            bonus += 0.25
        if any(token in q for token in _VISUAL_TOKENS) and record.id == "toolchain:antigravity":
            bonus += 0.35
        if record.tool_kind == "skill":
            bonus -= 0.05
        return (hit.rrf_score + bonus, hit.semantic_score, hit.bm25_score)

    return sorted(hits, key=_score, reverse=True)
