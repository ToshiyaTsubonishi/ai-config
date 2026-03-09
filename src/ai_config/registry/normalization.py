"""Normalization helpers for registry and retrieval metadata."""

from __future__ import annotations

from typing import Iterable


TARGET_ALIASES = {
    "codex": "codex",
    "gemini": "gemini_cli",
    "gemini_cli": "gemini_cli",
    "antigravity": "antigravity",
}

EXECUTION_TARGETS = frozenset(TARGET_ALIASES)


def normalize_target(target: str) -> str:
    """Normalize equivalent target labels to a canonical value."""
    value = str(target or "").strip()
    if not value:
        return ""
    return TARGET_ALIASES.get(value, value)


def normalize_targets(values: Iterable[str]) -> list[str]:
    """Normalize and deduplicate a target collection."""
    normalized = {normalize_target(value) for value in values if normalize_target(value)}
    return sorted(normalized)

