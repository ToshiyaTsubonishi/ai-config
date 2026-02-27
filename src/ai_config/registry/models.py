"""Data models for the tool registry."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class ToolRecord:
    """Normalized representation of a tool (Skill or MCP Server).

    This is the universal unit stored in the registry index.
    """

    id: str  # e.g. "skill:deep-research" or "mcp:firebase"
    name: str
    description: str
    tool_type: str  # "skill" | "mcp_server"
    source_path: str  # relative path from repo root
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = field(default=None, repr=False)

    # ---------- Derived helpers ----------

    @property
    def search_text(self) -> str:
        """Text blob used for both embedding and BM25 tokenisation."""
        parts = [self.name, self.description]
        # Include tag-like metadata if present
        if layer := self.metadata.get("layer"):
            parts.append(f"layer:{layer}")
        if targets := self.metadata.get("enabled_targets"):
            parts.extend(f"target:{t}" for t in targets)
        return " ".join(parts)

    # ---------- Serialisation ----------

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("embedding", None)  # never persist embeddings in JSON
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ToolRecord:
        data.pop("embedding", None)
        return cls(**data)


def save_records(records: list[ToolRecord], path: str) -> None:
    """Persist records as JSON (without embeddings)."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump([r.to_dict() for r in records], f, ensure_ascii=False, indent=2)


def load_records(path: str) -> list[ToolRecord]:
    """Load records from JSON."""
    with open(path, encoding="utf-8") as f:
        return [ToolRecord.from_dict(d) for d in json.load(f)]
