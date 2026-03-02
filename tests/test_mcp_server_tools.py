"""Tests for MCP server tools (ToolIndex)."""

from __future__ import annotations

import json
from pathlib import Path

from ai_config.mcp_server.tools import ToolIndex
from ai_config.registry.models import ToolRecord, save_records


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _make_records() -> list[ToolRecord]:
    return [
        ToolRecord(
            id="skill:deep-research",
            name="deep-research",
            description="Web調査を複数ステップで実行し、出典付きの調査レポートを作成する",
            source_path="skills/custom/deep-research/SKILL.md",
            tool_kind="skill",
            metadata={"layer": "custom"},
            tags=["layer:custom", "skill:deep-research"],
        ),
        ToolRecord(
            id="mcp:firecrawl",
            name="firecrawl",
            description="Firecrawl handles all web operations with superior accuracy",
            source_path="config/master/ai-sync.yaml",
            tool_kind="mcp_server",
            metadata={"layer": "external"},
            invoke={"backend": "mcp", "command": "npx", "args": ["-y", "firecrawl"]},
        ),
        ToolRecord(
            id="skill:code-review",
            name="code-review",
            description="Review code changes with a senior engineer lens",
            source_path="skills/shared/code-review/SKILL.md",
            tool_kind="skill",
            metadata={"layer": "shared"},
            tags=["layer:shared"],
        ),
    ]


def test_tool_index_search_keyword_fallback(tmp_path: Path) -> None:
    records = _make_records()
    save_records(records, str(tmp_path / "records.json"))

    index = ToolIndex(tmp_path)
    results = index.search("web 調査 research", top_k=3)

    assert len(results) > 0
    # deep-research should match because it mentions web and 調査
    ids = [r["id"] for r in results]
    assert "skill:deep-research" in ids


def test_tool_index_get_detail_found(tmp_path: Path) -> None:
    records = _make_records()
    save_records(records, str(tmp_path / "records.json"))

    index = ToolIndex(tmp_path)
    detail = index.get_detail("mcp:firecrawl")

    assert detail is not None
    assert detail["name"] == "firecrawl"
    assert detail["tool_kind"] == "mcp_server"


def test_tool_index_get_detail_not_found(tmp_path: Path) -> None:
    records = _make_records()
    save_records(records, str(tmp_path / "records.json"))

    index = ToolIndex(tmp_path)
    detail = index.get_detail("nonexistent:tool")
    assert detail is None


def test_tool_index_get_categories(tmp_path: Path) -> None:
    records = _make_records()
    save_records(records, str(tmp_path / "records.json"))

    index = ToolIndex(tmp_path)
    cats = index.get_categories()

    assert cats["total_tools"] == 3
    assert cats["by_kind"]["skill"] == 2
    assert cats["by_kind"]["mcp_server"] == 1
    assert cats["by_layer"]["custom"] == 1
    assert cats["by_layer"]["shared"] == 1
    assert cats["by_layer"]["external"] == 1


def test_tool_index_empty_index(tmp_path: Path) -> None:
    index = ToolIndex(tmp_path)
    results = index.search("anything")
    assert results == []

    cats = index.get_categories()
    assert cats["total_tools"] == 0
