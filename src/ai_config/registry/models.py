"""Data models for the tool registry."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any


TOOL_KIND_ALIASES = {
    "skill": "skill",
    "mcp_server": "mcp_server",
    "toolchain_adapter": "toolchain_adapter",
    "skill_script": "skill_script",
}


@dataclass
class ToolRecord:
    """Normalized representation of a tool unit in the registry index."""

    id: str  # e.g. "skill:deep-research", "mcp:firecrawl", "toolchain:codex"
    name: str
    description: str
    source_path: str  # relative path from repo root
    tool_kind: str = "skill"  # skill | skill_script | mcp_server | toolchain_adapter
    # Legacy compatibility: historic field persisted in v1/v2 records.
    tool_type: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    invoke: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    embedding: list[float] | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        # Backward compatibility with old records using tool_type.
        if not self.tool_kind and self.tool_type:
            self.tool_kind = TOOL_KIND_ALIASES.get(self.tool_type, self.tool_type)
        if not self.tool_type:
            self.tool_type = self.tool_kind
        self.tool_kind = TOOL_KIND_ALIASES.get(self.tool_kind, self.tool_kind)
        if not isinstance(self.tags, list):
            self.tags = []
        if not isinstance(self.invoke, dict):
            self.invoke = {}
        if not isinstance(self.metadata, dict):
            self.metadata = {}

    @property
    def search_text(self) -> str:
        """Text blob used for both embedding and BM25 tokenization."""
        parts: list[str] = [
            self.name,
            self.description,
            f"tool_kind:{self.tool_kind}",
        ]

        if self.tags:
            parts.extend(self.tags)

        # Include tag-like metadata if present.
        if layer := self.metadata.get("layer"):
            parts.append(f"layer:{layer}")
        if source_repo := self.metadata.get("source_repo"):
            parts.append(f"source_repo:{source_repo}")
        if domain := self.metadata.get("domain"):
            parts.append(f"domain:{domain}")
        targets = self.metadata.get("enabled_targets", [])
        if isinstance(targets, list):
            parts.extend(f"target:{target}" for target in targets if target)
        capabilities = self.metadata.get("capabilities", [])
        if isinstance(capabilities, list):
            parts.extend(f"capability:{cap}" for cap in capabilities if cap)

        return " ".join(parts)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        # Never persist raw vectors in JSON.
        data.pop("embedding", None)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ToolRecord:
        payload = dict(data)
        payload.pop("embedding", None)
        if "tool_kind" not in payload and "tool_type" in payload:
            payload["tool_kind"] = TOOL_KIND_ALIASES.get(payload["tool_type"], payload["tool_type"])
        return cls(**payload)


def save_records(records: list[ToolRecord], path: str) -> None:
    """Persist records as JSON (without embeddings)."""
    with open(path, "w", encoding="utf-8") as file:
        json.dump([record.to_dict() for record in records], file, ensure_ascii=False, indent=2)


def load_records(path: str) -> list[ToolRecord]:
    """Load records from JSON."""
    with open(path, encoding="utf-8") as file:
        raw = json.load(file)
    return [ToolRecord.from_dict(entry) for entry in raw]
