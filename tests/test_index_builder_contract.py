from __future__ import annotations

import json
from pathlib import Path

from ai_config.registry.index_builder import build_index
from ai_config.registry.models import ToolRecord


def test_index_builder_writes_v3_contract_artifacts(tmp_path: Path) -> None:
    records = [
        ToolRecord(
            id="skill:test",
            name="test-skill",
            description="test skill description",
            source_path="skills/shared/test/SKILL.md",
            tool_kind="skill",
            tags=["layer:shared"],
        ),
        ToolRecord(
            id="mcp:firecrawl",
            name="firecrawl",
            description="web crawl",
            source_path="config/master/ai-sync.yaml",
            tool_kind="mcp_server",
            invoke={"backend": "mcp", "command": "npx", "args": ["-y", "firecrawl"], "env_keys": []},
        ),
    ]

    build_index(records, tmp_path, embedding_backend="hash", vector_backend="numpy")

    for artifact in ("faiss.bin", "bm25.pkl", "keyword_index.json", "records.json", "summary.json"):
        assert (tmp_path / artifact).exists(), artifact

    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["index_format_version"] == 3
    for key in ("index_format_version", "embedding_backend", "vector_backend", "embedding_dim", "profile"):
        assert key in summary
