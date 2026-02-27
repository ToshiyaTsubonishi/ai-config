"""Index builder: creates FAISS vector index and BM25 keyword index.

Reads all ToolRecords from skill and MCP parsers, encodes them,
and persists indexes to .index/ directory.
"""

from __future__ import annotations

import json
import logging
import pickle
from pathlib import Path

import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from ai_config.registry.models import ToolRecord, save_records

logger = logging.getLogger(__name__)

DEFAULT_INDEX_DIR = ".index"
EMBEDDING_MODEL = "intfloat/multilingual-e5-small"


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + lowering tokenizer for BM25."""
    return text.lower().split()


def build_index(
    records: list[ToolRecord],
    index_dir: Path,
    model_name: str = EMBEDDING_MODEL,
) -> None:
    """Build and save FAISS + BM25 indexes from ToolRecords.

    Outputs:
      - index_dir/faiss.bin   – FAISS flat L2 index
      - index_dir/bm25.pkl   – pickled BM25Okapi instance
      - index_dir/records.json – serialised ToolRecords (no embeddings)
    """
    if not records:
        logger.warning("No records to index")
        return

    index_dir.mkdir(parents=True, exist_ok=True)

    # ---------- 1. Encode embeddings ----------
    logger.info("Loading embedding model: %s", model_name)
    model = SentenceTransformer(model_name)

    texts = [r.search_text for r in records]
    logger.info("Encoding %d records…", len(texts))
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)
    embeddings = np.asarray(embeddings, dtype=np.float32)

    # Attach embeddings to records (in-memory only)
    for rec, emb in zip(records, embeddings):
        rec.embedding = emb.tolist()

    # ---------- 2. Build FAISS index ----------
    dim = embeddings.shape[1]
    faiss_index = faiss.IndexFlatIP(dim)  # inner product (cosine with normalised vecs)
    faiss_index.add(embeddings)

    faiss_path = index_dir / "faiss.bin"
    faiss.write_index(faiss_index, str(faiss_path))
    logger.info("FAISS index saved: %s (%d vectors, dim=%d)", faiss_path, faiss_index.ntotal, dim)

    # ---------- 3. Build BM25 index ----------
    tokenized = [_tokenize(t) for t in texts]
    bm25 = BM25Okapi(tokenized)

    bm25_path = index_dir / "bm25.pkl"
    with open(bm25_path, "wb") as f:
        pickle.dump(bm25, f)
    logger.info("BM25 index saved: %s", bm25_path)

    # ---------- 4. Save records ----------
    records_path = index_dir / "records.json"
    save_records(records, str(records_path))
    logger.info("Records saved: %s (%d entries)", records_path, len(records))

    # ---------- 5. Write summary ----------
    summary = {
        "total_records": len(records),
        "skills": sum(1 for r in records if r.tool_type == "skill"),
        "mcp_servers": sum(1 for r in records if r.tool_type == "mcp_server"),
        "embedding_model": model_name,
        "embedding_dim": dim,
    }
    summary_path = index_dir / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    logger.info("Index build complete: %s", summary)
