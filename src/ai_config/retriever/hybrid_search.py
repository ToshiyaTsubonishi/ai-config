"""Hybrid search retriever with Reciprocal Rank Fusion (RRF).

Combines:
  - FAISS cosine similarity (semantic)
  - BM25Okapi (keyword / exact match)

Fuses ranked lists using RRF: score(d) = Σ 1/(k + rank_i(d))
"""

from __future__ import annotations

import logging
import pickle
from pathlib import Path

import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from ai_config.registry.index_builder import DEFAULT_INDEX_DIR, EMBEDDING_MODEL
from ai_config.registry.models import ToolRecord, load_records

logger = logging.getLogger(__name__)

# RRF constant – standard value from the original RRF paper (Cormack et al.)
RRF_K = 60


class HybridRetriever:
    """Loads pre-built indexes and performs hybrid retrieval."""

    def __init__(self, index_dir: str | Path, model_name: str = EMBEDDING_MODEL):
        index_dir = Path(index_dir)

        # Load records
        self.records = load_records(str(index_dir / "records.json"))
        logger.info("Loaded %d tool records", len(self.records))

        # Load FAISS
        self.faiss_index = faiss.read_index(str(index_dir / "faiss.bin"))
        logger.info("FAISS index loaded: %d vectors", self.faiss_index.ntotal)

        # Load BM25
        with open(index_dir / "bm25.pkl", "rb") as f:
            self.bm25: BM25Okapi = pickle.load(f)

        # Load embedding model (reuse same model used at build time)
        self.model = SentenceTransformer(model_name)

    def search(
        self,
        query: str,
        top_k: int = 10,
        semantic_k: int = 30,
        bm25_k: int = 30,
    ) -> list[tuple[ToolRecord, float]]:
        """Retrieve top-K tools for a given query using hybrid RRF.

        Args:
            query: Natural language query.
            top_k: Number of final results to return.
            semantic_k: Candidates from FAISS.
            bm25_k: Candidates from BM25.

        Returns:
            List of (ToolRecord, rrf_score) sorted by descending score.
        """
        if not self.records:
            return []

        # ---------- Semantic search (FAISS) ----------
        q_emb = self.model.encode([query], normalize_embeddings=True)
        q_emb = np.asarray(q_emb, dtype=np.float32)
        scores_faiss, indices_faiss = self.faiss_index.search(q_emb, min(semantic_k, len(self.records)))

        faiss_ranking: list[int] = []
        for idx in indices_faiss[0]:
            if idx >= 0:  # FAISS returns -1 for padding
                faiss_ranking.append(int(idx))

        # ---------- BM25 search ----------
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query)
        bm25_top_idx = np.argsort(bm25_scores)[::-1][:bm25_k].tolist()

        bm25_ranking: list[int] = [i for i in bm25_top_idx if bm25_scores[i] > 0]

        # ---------- Reciprocal Rank Fusion ----------
        rrf_scores: dict[int, float] = {}

        for rank, idx in enumerate(faiss_ranking):
            rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 1.0 / (RRF_K + rank + 1)

        for rank, idx in enumerate(bm25_ranking):
            rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 1.0 / (RRF_K + rank + 1)

        # Sort by fused score
        sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        results = []
        for idx, score in sorted_items[:top_k]:
            results.append((self.records[idx], score))

        return results

    def search_text(self, query: str, top_k: int = 10) -> str:
        """Convenience: return formatted string of search results."""
        results = self.search(query, top_k=top_k)
        if not results:
            return "No tools found."

        lines = []
        for i, (rec, score) in enumerate(results, 1):
            lines.append(
                f"{i}. [{rec.tool_type}] {rec.name} (score={score:.4f})\n"
                f"   {rec.description[:120]}\n"
                f"   id={rec.id}  source={rec.source_path}"
            )
        return "\n\n".join(lines)
