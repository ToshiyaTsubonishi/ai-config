"""Hybrid search retriever with Reciprocal Rank Fusion (RRF)."""

from __future__ import annotations

import json
import logging
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from rank_bm25 import BM25Okapi

from ai_config.registry.index_builder import EMBEDDING_DIM, EMBEDDING_MODEL
from ai_config.registry.models import ToolRecord, load_records
from ai_config.registry.normalization import normalize_targets

logger = logging.getLogger(__name__)

SUPPORTED_EMBEDDING_BACKENDS = {"sentence_transformer", "hash"}
SUPPORTED_VECTOR_BACKENDS = {"faiss", "numpy"}
MIN_SUPPORTED_INDEX_FORMAT = 3


def _tokenize(text: str) -> list[str]:
    return [tok for tok in text.lower().split() if tok]


def _infer_source_repo_from_source_path(source_path: str) -> str:
    parts = source_path.split("/")
    if len(parts) >= 3 and parts[0] == "skills" and parts[1] == "external":
        return parts[2]
    if len(parts) >= 5 and parts[0] == "skills" and parts[1] == "imported" and parts[2] == "skills-sh" and parts[3] == "sources":
        return parts[4]
    if len(parts) >= 3 and parts[0] == "skills" and parts[1] == "imported":
        return parts[2]
    if len(parts) >= 2 and parts[0] == "skills":
        return "local"
    if len(parts) >= 2 and parts[0] == "config":
        return "managed"
    return "unknown"


def _hash_embedding(text: str, dim: int) -> np.ndarray:
    vec = np.zeros((dim,), dtype=np.float32)
    for token in _tokenize(text):
        h = hash(token)
        idx = h % dim
        sign = 1.0 if (h & 1) == 0 else -1.0
        vec[idx] += sign
    norm = np.linalg.norm(vec)
    if norm == 0:
        norm = 1.0
    return vec / norm


@dataclass
class SearchHit:
    record: ToolRecord
    rrf_score: float
    semantic_score: float
    bm25_score: float
    semantic_rank: int | None
    bm25_rank: int | None
    keyword_rank: int | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.record.id,
            "name": self.record.name,
            "description": self.record.description,
            "tool_kind": self.record.tool_kind,
            "source_path": self.record.source_path,
            "score": self.rrf_score,
            "score_breakdown": {
                "rrf": self.rrf_score,
                "semantic": self.semantic_score,
                "bm25": self.bm25_score,
                "semantic_rank": self.semantic_rank,
                "bm25_rank": self.bm25_rank,
                "keyword_rank": self.keyword_rank,
            },
            "tags": self.record.tags,
            "metadata": self.record.metadata,
            "invoke": self.record.invoke,
        }


class HybridRetriever:
    """Load prebuilt artifacts and execute hybrid retrieval."""

    def __init__(self, index_dir: str | Path, model_name: str = EMBEDDING_MODEL):
        self.index_dir = Path(index_dir)
        summary_path = self.index_dir / "summary.json"
        if not summary_path.exists():
            raise FileNotFoundError(f"summary.json not found: {summary_path}")

        with open(summary_path, encoding="utf-8") as f:
            summary = json.load(f)

        self.index_format_version = int(summary.get("index_format_version", 0))
        if self.index_format_version < MIN_SUPPORTED_INDEX_FORMAT:
            raise ValueError(
                f"Unsupported index_format_version={self.index_format_version}. "
                f"Please rebuild index (required >= {MIN_SUPPORTED_INDEX_FORMAT})."
            )

        self.embedding_backend = str(summary.get("embedding_backend", "hash"))
        self.vector_backend = str(summary.get("vector_backend", "numpy"))
        self.embedding_dim = int(summary.get("embedding_dim", EMBEDDING_DIM))
        self.embedding_model = str(summary.get("embedding_model") or model_name)
        if self.embedding_backend not in SUPPORTED_EMBEDDING_BACKENDS:
            raise ValueError(f"Unsupported embedding backend: {self.embedding_backend}")
        if self.vector_backend not in SUPPORTED_VECTOR_BACKENDS:
            raise ValueError(f"Unsupported vector backend: {self.vector_backend}")

        self.records = load_records(str(self.index_dir / "records.json"))
        with open(self.index_dir / "bm25.pkl", "rb") as f:
            self.bm25: BM25Okapi = pickle.load(f)
        with open(self.index_dir / "keyword_index.json", encoding="utf-8") as f:
            self.keyword_index: dict[str, Any] = json.load(f)

        vector_path = self.index_dir / "faiss.bin"
        self.faiss_index = None
        self.vector_matrix: np.ndarray | None = None
        if self.vector_backend == "faiss":
            import faiss  # type: ignore

            self.faiss_index = faiss.read_index(str(vector_path))
        else:
            with open(vector_path, "rb") as f:
                self.vector_matrix = np.asarray(np.load(f), dtype=np.float32)

        self.model = None
        if self.embedding_backend == "sentence_transformer":
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(self.embedding_model)

    def _build_query_vector(self, query: str) -> np.ndarray:
        if self.embedding_backend == "sentence_transformer":
            assert self.model is not None
            vec = self.model.encode([query], normalize_embeddings=True)
            return np.asarray(vec[0], dtype=np.float32)
        return _hash_embedding(query, self.embedding_dim)

    def _keyword_hits(self, query: str) -> list[int]:
        token_to_ids = self.keyword_index.get("token_to_ids", {})
        exact_name_to_ids = self.keyword_index.get("exact_name_to_ids", {})
        exact_id_to_id = self.keyword_index.get("exact_id_to_id", {})
        id_to_index = {r.id: i for i, r in enumerate(self.records)}

        hits: list[str] = []
        q = query.lower().strip()
        if q in exact_name_to_ids:
            hits.extend(exact_name_to_ids[q])
        if q in exact_id_to_id:
            hits.append(exact_id_to_id[q])
        for token in _tokenize(query):
            hits.extend(token_to_ids.get(token, []))

        ordered: list[int] = []
        seen: set[int] = set()
        for tool_id in hits:
            idx = id_to_index.get(tool_id)
            if idx is None or idx in seen:
                continue
            seen.add(idx)
            ordered.append(idx)
        return ordered

    @staticmethod
    def _matches_filters(
        record: ToolRecord,
        tool_kinds: set[str] | None,
        targets: set[str] | None,
        capabilities: set[str] | None,
        source_repos: set[str] | None,
        domains: set[str] | None,
        executable_only: bool,
    ) -> bool:
        if executable_only and record.metadata.get("executable", True) is False:
            return False
        if tool_kinds and record.tool_kind not in tool_kinds:
            return False
        if targets:
            target_values = set(normalize_targets(record.metadata.get("enabled_targets", []) or []))
            tag_targets = normalize_targets(tag.split(":", 1)[1] for tag in record.tags if tag.startswith("target:"))
            target_values.update(tag_targets)
            if not target_values.intersection(normalize_targets(targets)):
                return False
        if capabilities:
            caps = set(record.metadata.get("capabilities", []) or [])
            caps.update(tag.split(":", 1)[1] for tag in record.tags if tag.startswith("capability:"))
            if not caps.intersection(capabilities):
                return False
        if source_repos:
            source_repo = str(record.metadata.get("source_repo") or _infer_source_repo_from_source_path(record.source_path))
            if source_repo not in source_repos:
                return False
        if domains:
            domain = str(record.metadata.get("domain") or "")
            if not domain or domain not in domains:
                return False
        return True

    def search(
        self,
        query: str,
        top_k: int = 8,
        semantic_k: int = 30,
        bm25_k: int = 30,
        rrf_k: int = 60,
        tool_kinds: list[str] | None = None,
        targets: list[str] | None = None,
        capabilities: list[str] | None = None,
        source_repos: list[str] | None = None,
        domains: list[str] | None = None,
        executable_only: bool = False,
    ) -> list[SearchHit]:
        if not self.records:
            return []

        query_vec = self._build_query_vector(query)

        # semantic
        semantic_ranking: list[int] = []
        semantic_scores: dict[int, float] = {}
        if self.vector_backend == "faiss":
            assert self.faiss_index is not None
            scores, indices = self.faiss_index.search(
                np.asarray([query_vec], dtype=np.float32), min(semantic_k, len(self.records))
            )
            for idx, score in zip(indices[0], scores[0]):
                if idx < 0:
                    continue
                semantic_ranking.append(int(idx))
                semantic_scores[int(idx)] = float(score)
        else:
            assert self.vector_matrix is not None
            sims = self.vector_matrix @ query_vec
            top_idx = np.argsort(sims)[::-1][: min(semantic_k, len(self.records))]
            for idx in top_idx:
                ii = int(idx)
                semantic_ranking.append(ii)
                semantic_scores[ii] = float(sims[ii])

        # bm25
        bm25_values = self.bm25.get_scores(_tokenize(query))
        bm25_top = np.argsort(bm25_values)[::-1][: min(bm25_k, len(self.records))]
        bm25_ranking = [int(i) for i in bm25_top if bm25_values[int(i)] > 0]
        bm25_scores = {int(i): float(bm25_values[int(i)]) for i in bm25_ranking}

        # keyword exact
        keyword_ranking = self._keyword_hits(query)

        kind_filter = set(tool_kinds or []) or None
        target_filter = set(targets or []) or None
        cap_filter = set(capabilities or []) or None
        source_filter = set(source_repos or []) or None
        domain_filter = set(domains or []) or None

        rrf_scores: dict[int, float] = {}
        semantic_rank_map: dict[int, int] = {}
        bm25_rank_map: dict[int, int] = {}
        keyword_rank_map: dict[int, int] = {}

        for rank, idx in enumerate(semantic_ranking, start=1):
            rec = self.records[idx]
            if not self._matches_filters(
                rec,
                kind_filter,
                target_filter,
                cap_filter,
                source_filter,
                domain_filter,
                executable_only,
            ):
                continue
            semantic_rank_map[idx] = rank
            rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 1.0 / (rrf_k + rank)

        for rank, idx in enumerate(bm25_ranking, start=1):
            rec = self.records[idx]
            if not self._matches_filters(
                rec,
                kind_filter,
                target_filter,
                cap_filter,
                source_filter,
                domain_filter,
                executable_only,
            ):
                continue
            bm25_rank_map[idx] = rank
            rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 1.0 / (rrf_k + rank)

        for rank, idx in enumerate(keyword_ranking, start=1):
            rec = self.records[idx]
            if not self._matches_filters(
                rec,
                kind_filter,
                target_filter,
                cap_filter,
                source_filter,
                domain_filter,
                executable_only,
            ):
                continue
            keyword_rank_map[idx] = rank
            rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 1.0 / (rrf_k + rank)

        ordered = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        hits: list[SearchHit] = []
        for idx, rrf_score in ordered:
            hits.append(
                SearchHit(
                    record=self.records[idx],
                    rrf_score=float(rrf_score),
                    semantic_score=float(semantic_scores.get(idx, 0.0)),
                    bm25_score=float(bm25_scores.get(idx, 0.0)),
                    semantic_rank=semantic_rank_map.get(idx),
                    bm25_rank=bm25_rank_map.get(idx),
                    keyword_rank=keyword_rank_map.get(idx),
                )
            )
        return hits

    def search_text(self, query: str, top_k: int = 8) -> str:
        hits = self.search(query=query, top_k=top_k)
        if not hits:
            return "No tools found."

        lines: list[str] = []
        for i, hit in enumerate(hits, start=1):
            lines.append(
                f"{i}. [{hit.record.tool_kind}] {hit.record.name} (rrf={hit.rrf_score:.4f}, "
                f"sem={hit.semantic_score:.4f}, bm25={hit.bm25_score:.4f})\n"
                f"   {hit.record.description[:120]}\n"
                f"   id={hit.record.id} source={hit.record.source_path}"
            )
        return "\n\n".join(lines)
