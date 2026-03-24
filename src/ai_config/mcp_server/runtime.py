"""Runtime validation helpers for selector-serving deployments."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ai_config.retriever.hybrid_search import HybridRetriever

REQUIRED_INDEX_ARTIFACTS = (
    "summary.json",
    "records.json",
    "bm25.pkl",
    "keyword_index.json",
    "faiss.bin",
)


@dataclass(frozen=True)
class RuntimeIndexStatus:
    """Validated runtime index metadata for health/readiness reporting."""

    index_dir: str
    record_count: int
    index_format_version: int
    profile: str
    embedding_backend: str
    vector_backend: str

    def to_readiness_payload(self) -> dict[str, Any]:
        return {
            "status": "ready",
            "surface": "selector-serving",
            "runtime_mode": "read_only",
            "index_dir": self.index_dir,
            "record_count": self.record_count,
            "index_format_version": self.index_format_version,
            "profile": self.profile,
            "embedding_backend": self.embedding_backend,
            "vector_backend": self.vector_backend,
            "required_artifacts": list(REQUIRED_INDEX_ARTIFACTS),
        }


def required_artifact_paths(index_dir: Path) -> list[Path]:
    resolved = index_dir.resolve()
    return [resolved / artifact for artifact in REQUIRED_INDEX_ARTIFACTS]


def validate_runtime_index(index_dir: Path) -> RuntimeIndexStatus:
    """Validate that all required selector artifacts are present and loadable."""
    resolved = index_dir.resolve()
    missing = [str(path) for path in required_artifact_paths(resolved) if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing required index artifacts for runtime serving: " + ", ".join(missing)
        )

    summary_path = resolved / "summary.json"
    records_path = resolved / "records.json"

    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except Exception as error:
        raise ValueError(f"Invalid summary.json at {summary_path}: {error}") from error
    if not isinstance(summary, dict):
        raise ValueError(f"Invalid summary.json at {summary_path}: expected JSON object.")

    try:
        raw_records = json.loads(records_path.read_text(encoding="utf-8"))
    except Exception as error:
        raise ValueError(f"Invalid records.json at {records_path}: {error}") from error
    if not isinstance(raw_records, list):
        raise ValueError(f"Invalid records.json at {records_path}: expected JSON array.")

    retriever = HybridRetriever(resolved)
    return RuntimeIndexStatus(
        index_dir=str(resolved),
        record_count=len(retriever.records),
        index_format_version=int(summary.get("index_format_version", 0)),
        profile=str(summary.get("profile") or "unknown"),
        embedding_backend=str(summary.get("embedding_backend") or "unknown"),
        vector_backend=str(summary.get("vector_backend") or "unknown"),
    )
