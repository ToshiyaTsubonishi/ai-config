"""Helpers for inferring source/domain metadata from skills tree paths."""

from __future__ import annotations

from pathlib import Path


def infer_source_repo_and_domain(skills_rel_path: Path) -> tuple[str, str]:
    parts = skills_rel_path.parts
    if not parts:
        return "unknown", "unknown"

    layer = parts[0]
    if layer == "external":
        source_repo = parts[1] if len(parts) > 1 else "unknown"
        domain = "general"
        if len(parts) > 2:
            domain_hint = parts[2]
            if domain_hint in {"skills", "skill", "sources"} and len(parts) > 3:
                domain_hint = parts[3]
            domain = domain_hint
        return source_repo, domain

    if layer == "official":
        source_repo = parts[1] if len(parts) > 1 else "official"
        domain = "official"
        if len(parts) > 2:
            domain_hint = parts[2]
            if domain_hint in {"skills", "skill", "sources"} and len(parts) > 3:
                domain_hint = parts[3]
            domain = domain_hint
        return source_repo, domain

    if layer == "imported":
        source_repo = parts[1] if len(parts) > 1 else "imported"
        domain = source_repo
        if len(parts) > 3 and parts[2] == "sources":
            source_repo = parts[3]
        return source_repo, domain

    # local layers: shared/custom/codex/gemini/antigravity
    # Accept optional domain layout:
    #   skills/custom/<domain>/<skill>/SKILL.md
    #   skills/shared/<domain>/<skill>/SKILL.md
    if len(parts) >= 4 and parts[1] not in {"scripts"}:
        return "local", parts[1]
    return "local", layer
