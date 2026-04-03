from __future__ import annotations

from pathlib import Path

from ai_config.registry.index_builder import build_index
from ai_config.registry.models import ToolRecord
from ai_config.retriever.hybrid_search import HybridRetriever


def _build_sample_index(index_dir: Path) -> None:
    records = [
        ToolRecord(
            id="skill:deploy",
            name="deploy-tool",
            description="deploy service application",
            source_path="skills/shared/deploy/SKILL.md",
            tool_kind="skill",
            tags=["capability:deployment"],
        ),
        ToolRecord(
            id="mcp:settings",
            name="settings-mcp",
            description="MCP settings and configuration",
            source_path="config/master/ai-sync.yaml",
            tool_kind="mcp_server",
            metadata={"enabled_targets": ["codex"]},
            tags=["target:codex"],
        ),
        ToolRecord(
            id="skill_script:run",
            name="runner-script",
            description="run helper script",
            source_path="skills/codex/demo/scripts/run.py",
            tool_kind="skill_script",
            tags=["target:codex"],
        ),
        ToolRecord(
            id="mcp_catalog:demo:plugins:data:bigquery",
            name="bigquery-catalog",
            description="catalog-only mcp",
            source_path="skills/external/anthropics-knowledge-work-plugins/data/.mcp.json",
            tool_kind="mcp_server",
            metadata={"catalog_only": True, "executable": False},
        ),
    ]
    build_index(records, index_dir, embedding_backend="hash", vector_backend="numpy")


def test_rrf_and_filters(tmp_path: Path) -> None:
    _build_sample_index(tmp_path)
    retriever = HybridRetriever(tmp_path)

    hits = retriever.search("deploy application", top_k=3)
    assert hits
    assert hits[0].record.id == "skill:deploy"
    assert hits[0].semantic_score >= 0

    mcp_only = retriever.search("settings config", top_k=5, tool_kinds=["mcp_server"])
    assert mcp_only
    assert all(h.record.tool_kind == "mcp_server" for h in mcp_only)

    codex_only = retriever.search("run codex helper", top_k=5, targets=["codex"])
    assert codex_only
    assert all(
        "codex" in (h.record.metadata.get("enabled_targets", []) or [])
        or any(tag == "target:codex" for tag in h.record.tags)
        for h in codex_only
    )

    exec_only = retriever.search("bigquery", top_k=10, executable_only=True)
    assert all(h.record.metadata.get("executable", True) is not False for h in exec_only)


def test_rrf_handles_japanese_queries_without_spaces(tmp_path: Path) -> None:
    records = [
        ToolRecord(
            id="skill:japanese-research",
            name="japanese-research",
            description="日本語の調査手順を整理するガイド",
            source_path="skills/shared/japanese-research/SKILL.md",
            tool_kind="skill",
            tags=["capability:research"],
        ),
        ToolRecord(
            id="skill:english-review",
            name="english-review",
            description="Review code changes with a senior engineer lens",
            source_path="skills/shared/english-review/SKILL.md",
            tool_kind="skill",
            tags=["capability:review"],
        ),
    ]
    build_index(records, tmp_path, embedding_backend="hash", vector_backend="numpy")

    retriever = HybridRetriever(tmp_path)
    hits = retriever.search("日本語調査", top_k=2)

    assert hits
    assert hits[0].record.id == "skill:japanese-research"
