from __future__ import annotations

from ai_config.tokenization import tokenize_for_search


def test_tokenize_for_search_splits_japanese_terms() -> None:
    tokens = tokenize_for_search("国家公務員")

    assert "国家" in tokens
    assert "公務員" in tokens


def test_tokenize_for_search_includes_normalized_form() -> None:
    tokens = tokenize_for_search("附属")

    assert "附属" in tokens
    assert "付属" in tokens


def test_tokenize_for_search_preserves_structured_ascii_tokens() -> None:
    tokens = tokenize_for_search("target:codex で ai-config-selector と mcp:firecrawl を使う")

    assert "target:codex" in tokens
    assert "ai-config-selector" in tokens
    assert "mcp:firecrawl" in tokens


def test_tokenize_for_search_keeps_duplicate_terms() -> None:
    tokens = tokenize_for_search("調査 調査")

    assert tokens.count("調査") == 2


def test_tokenize_for_search_avoids_duplicate_normalized_tokens() -> None:
    tokens = tokenize_for_search("公務員")

    assert tokens.count("公務員") == 1
