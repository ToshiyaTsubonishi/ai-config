"""MCP tool definitions for dynamic tool selection.

Provides tools for AI agents to search, discover, and retrieve tool
details from the ai-config registry without loading all tools into
the agent's context window.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ai_config.registry.models import ToolRecord, load_records
from ai_config.tokenization import tokenize_for_search

logger = logging.getLogger(__name__)

# Maximum items returned by search_tools to keep context small
DEFAULT_TOP_K = 5
MAX_DESCRIPTION_LENGTH = 200


class ToolIndex:
    """In-memory tool index backed by the hybrid search engine."""

    def __init__(self, index_dir: Path) -> None:
        self._index_dir = index_dir
        self._records: list[ToolRecord] = []
        self._searcher: Any = None
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return

        records_path = self._index_dir / "records.json"
        if not records_path.exists():
            logger.warning("records.json not found at %s", records_path)
            self._loaded = True
            return

        self._records = load_records(str(records_path))
        logger.info("Loaded %d tool records from %s", len(self._records), records_path)

        # Try to initialize hybrid search
        try:
            from ai_config.retriever.hybrid_search import HybridRetriever

            self._searcher = HybridRetriever(self._index_dir)
            logger.info("Hybrid search engine loaded successfully.")
        except Exception as e:
            logger.warning("Could not load hybrid search engine: %s – falling back to simple search.", e)

        self._loaded = True

    @property
    def records(self) -> list[ToolRecord]:
        self._ensure_loaded()
        return self._records

    def search(self, query: str, top_k: int = DEFAULT_TOP_K) -> list[dict[str, Any]]:
        """Search tools using hybrid search (vector + BM25 + RRF)."""
        self._ensure_loaded()

        if self._searcher is not None:
            try:
                hits = self._searcher.search(query, top_k=top_k)
                return [self._summarize(hit.to_dict()) for hit in hits]
            except Exception as e:
                logger.warning("Hybrid search failed: %s – falling back to keyword search.", e)

        # Fallback: simple keyword matching
        return self._keyword_search(query, top_k)

    def get_detail(self, tool_id: str) -> dict[str, Any] | None:
        """Get full detail for a specific tool by ID."""
        record = self.get_record(tool_id)
        return record.to_dict() if record is not None else None

    def get_record(self, tool_id: str) -> ToolRecord | None:
        """Get the raw ToolRecord for a specific tool by ID."""
        self._ensure_loaded()
        for record in self._records:
            if record.id == tool_id:
                return record
        return None

    def get_categories(self) -> dict[str, Any]:
        """Get summary of available tool categories."""
        self._ensure_loaded()

        by_kind: dict[str, int] = {}
        by_layer: dict[str, int] = {}
        for r in self._records:
            by_kind[r.tool_kind] = by_kind.get(r.tool_kind, 0) + 1
            layer = r.metadata.get("layer", "unknown")
            by_layer[layer] = by_layer.get(layer, 0) + 1

        return {
            "total_tools": len(self._records),
            "by_kind": by_kind,
            "by_layer": by_layer,
        }

    def _summarize(self, result: dict[str, Any]) -> dict[str, Any]:
        """Create a compact summary of a search result."""
        desc = result.get("description", "")
        if len(desc) > MAX_DESCRIPTION_LENGTH:
            desc = desc[:MAX_DESCRIPTION_LENGTH] + "..."
        return {
            "id": result.get("id", ""),
            "name": result.get("name", ""),
            "description": desc,
            "tool_kind": result.get("tool_kind", ""),
            "layer": result.get("metadata", {}).get("layer", "unknown"),
            "score": result.get("score", 0.0),
        }

    def _keyword_search(self, query: str, top_k: int) -> list[dict[str, Any]]:
        """Simple keyword-based search fallback."""
        query_tokens = {token for token in tokenize_for_search(query)}
        if not query_tokens:
            return []

        scored: list[tuple[float, ToolRecord]] = []
        for r in self._records:
            record_tokens = set(tokenize_for_search(r.search_text))
            score = len(query_tokens.intersection(record_tokens))
            if score > 0:
                scored.append((float(score), r))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [self._summarize(r.to_dict() | {"score": s}) for s, r in scored[:top_k]]
