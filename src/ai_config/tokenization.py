"""Shared tokenization helpers for BM25, keyword search, and hash embeddings."""

from __future__ import annotations

import re
from functools import lru_cache

STRUCTURED_ASCII_TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:[A-Za-z0-9:._/-]*[:._/-][A-Za-z0-9:._/-]*)+")
SEARCHABLE_TOKEN_RE = re.compile(r"[0-9A-Za-z\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]")


def _normalize_token(token: str) -> str:
    candidate = token.strip()
    if not candidate or not SEARCHABLE_TOKEN_RE.search(candidate):
        return ""
    if candidate.isascii():
        return candidate.lower()
    return candidate


@lru_cache(maxsize=1)
def _get_sudachi_tokenizer() -> object:
    from sudachipy import dictionary

    return dictionary.Dictionary(dict="core").create()


def _tokenize_segment(text: str) -> list[str]:
    if not text or text.isspace():
        return []

    from sudachipy import tokenizer

    tokens: list[str] = []
    sudachi = _get_sudachi_tokenizer()
    for morpheme in sudachi.tokenize(text, tokenizer.Tokenizer.SplitMode.B):
        surface = _normalize_token(morpheme.surface())
        if surface:
            tokens.append(surface)

        normalized = _normalize_token(morpheme.normalized_form())
        if normalized and normalized != surface:
            tokens.append(normalized)

    return tokens


def tokenize_for_search(text: str) -> list[str]:
    """Tokenize mixed Japanese/ASCII search text for retrieval use cases."""
    tokens: list[str] = []
    last_index = 0

    for match in STRUCTURED_ASCII_TOKEN_RE.finditer(text):
        tokens.extend(_tokenize_segment(text[last_index : match.start()]))

        structured = _normalize_token(match.group(0))
        if structured:
            tokens.append(structured)
        last_index = match.end()

    tokens.extend(_tokenize_segment(text[last_index:]))
    return tokens
