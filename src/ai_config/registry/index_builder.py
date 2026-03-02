"""Index builder for dynamic tool selection.

Artifacts:
  - faiss.bin           (FAISS index or numpy matrix payload)
  - bm25.pkl            (BM25Okapi)
  - keyword_index.json  (exact/token lookup)
  - records.json        (ToolRecord dump)
  - summary.json        (contract metadata)
"""

from __future__ import annotations

import json
import logging
import os
import pickle
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
from rank_bm25 import BM25Okapi

from ai_config.registry.models import ToolRecord

logger = logging.getLogger(__name__)

DEFAULT_INDEX_DIR = ".index"
EMBEDDING_MODEL = "intfloat/multilingual-e5-small"
EMBEDDING_DIM = 384
INDEX_FORMAT_VERSION = 3
EMBEDDING_BACKEND = os.getenv("AI_CONFIG_EMBEDDING_BACKEND", "hash")
VECTOR_BACKEND = os.getenv("AI_CONFIG_VECTOR_BACKEND", "numpy")


def _tokenize(text: str) -> list[str]:
    return [tok for tok in text.lower().split() if tok]


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent, delete=False) as tmp:
        tmp.write(payload)
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def _atomic_write_json(path: Path, payload: Any) -> None:
    data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    _atomic_write_bytes(path, data)


def _atomic_write_pickle(path: Path, payload: Any) -> None:
    data = pickle.dumps(payload)
    _atomic_write_bytes(path, data)


def _build_hash_embeddings(texts: list[str], dim: int = EMBEDDING_DIM) -> np.ndarray:
    vectors = np.zeros((len(texts), dim), dtype=np.float32)
    for i, text in enumerate(texts):
        for token in _tokenize(text):
            h = hash(token)
            idx = h % dim
            sign = 1.0 if (h & 1) == 0 else -1.0
            vectors[i, idx] += sign

    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms


def _keyword_index(records: list[ToolRecord]) -> dict[str, Any]:
    token_to_ids: dict[str, list[str]] = {}
    exact_name_to_ids: dict[str, list[str]] = {}
    exact_id_to_id: dict[str, str] = {}

    for record in records:
        exact_id_to_id[record.id.lower()] = record.id
        name_key = record.name.lower().strip()
        exact_name_to_ids.setdefault(name_key, []).append(record.id)

        seed_text = " ".join([record.id, record.name, record.description, " ".join(record.tags)])
        for token in _tokenize(seed_text):
            bucket = token_to_ids.setdefault(token, [])
            if record.id not in bucket:
                bucket.append(record.id)

    return {
        "token_to_ids": token_to_ids,
        "exact_name_to_ids": exact_name_to_ids,
        "exact_id_to_id": exact_id_to_id,
    }


def _vector_backend_write(index_dir: Path, embeddings: np.ndarray, vector_backend: str) -> str:
    vector_path = index_dir / "faiss.bin"
    if vector_backend == "faiss":
        try:
            import faiss  # type: ignore

            index = faiss.IndexFlatIP(embeddings.shape[1])
            index.add(embeddings)
            with tempfile.NamedTemporaryFile(prefix=".faiss.", suffix=".tmp", dir=index_dir, delete=False) as tmp:
                tmp_path = Path(tmp.name)
            faiss.write_index(index, str(tmp_path))
            tmp_path.replace(vector_path)
            logger.info("FAISS index saved: %s (vectors=%d, dim=%d)", vector_path, index.ntotal, embeddings.shape[1])
            return "faiss"
        except Exception as exc:
            logger.warning("FAISS unavailable (%s). Falling back to numpy vector backend.", exc)

    with tempfile.NamedTemporaryFile(prefix=".vec.", suffix=".tmp", dir=index_dir, delete=False) as tmp:
        tmp_path = Path(tmp.name)
    with open(tmp_path, "wb") as fh:
        np.save(fh, embeddings)
    tmp_path.replace(vector_path)
    logger.info("Numpy vector matrix saved: %s (vectors=%d, dim=%d)", vector_path, embeddings.shape[0], embeddings.shape[1])
    return "numpy"


def build_index(
    records: list[ToolRecord],
    index_dir: Path,
    model_name: str = EMBEDDING_MODEL,
    embedding_backend: str = EMBEDDING_BACKEND,
    vector_backend: str = VECTOR_BACKEND,
    profile: str = "default",
) -> None:
    """Build and persist index artifacts."""
    if not records:
        raise ValueError("No records provided for index build.")

    index_dir.mkdir(parents=True, exist_ok=True)
    texts = [r.search_text for r in records]

    if embedding_backend == "sentence_transformer":
        from sentence_transformers import SentenceTransformer

        logger.info("Encoding records with sentence_transformer model=%s", model_name)
        model = SentenceTransformer(model_name)
        embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)
        embeddings = np.asarray(embeddings, dtype=np.float32)
    else:
        logger.info("Encoding records with hash backend (dim=%d)", EMBEDDING_DIM)
        embeddings = _build_hash_embeddings(texts, EMBEDDING_DIM)

    for rec, emb in zip(records, embeddings):
        rec.embedding = emb.tolist()

    vector_backend_used = _vector_backend_write(index_dir, embeddings, vector_backend)

    bm25 = BM25Okapi([_tokenize(text) for text in texts])
    _atomic_write_pickle(index_dir / "bm25.pkl", bm25)

    keyword_index = _keyword_index(records)
    _atomic_write_json(index_dir / "keyword_index.json", keyword_index)

    records_json = [record.to_dict() for record in records]
    _atomic_write_json(index_dir / "records.json", records_json)

    summary = {
        "index_format_version": INDEX_FORMAT_VERSION,
        "profile": profile,
        "total_records": len(records),
        "skills": sum(1 for r in records if r.tool_kind == "skill"),
        "skill_scripts": sum(1 for r in records if r.tool_kind == "skill_script"),
        "mcp_servers": sum(1 for r in records if r.tool_kind == "mcp_server"),
        "toolchain_adapters": sum(1 for r in records if r.tool_kind == "toolchain_adapter"),
        "embedding_model": model_name if embedding_backend == "sentence_transformer" else "hash",
        "embedding_backend": embedding_backend,
        "vector_backend": vector_backend_used,
        "embedding_dim": int(embeddings.shape[1]),
    }
    _atomic_write_json(index_dir / "summary.json", summary)
    logger.info("Index build complete: %s", summary)
