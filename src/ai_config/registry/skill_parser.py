"""Parser for SKILL.md files under skills/ directories.

Walks the skills tree, extracts YAML frontmatter (name, description) and
markdown body, and produces ToolRecord instances.
"""

from __future__ import annotations

import logging
from pathlib import Path

try:
    import frontmatter  # type: ignore
except Exception:  # pragma: no cover - optional dependency fallback
    frontmatter = None

from ai_config.registry.path_metadata import infer_source_repo_and_domain
from ai_config.registry.models import ToolRecord
from ai_config.registry.normalization import normalize_target

logger = logging.getLogger(__name__)

# Skill layers expected at skills/<layer>/<skill-name>/SKILL.md
SKILL_LAYERS = ("shared", "external", "imported", "custom", "codex", "antigravity", "gemini")
TARGET_LAYERS = {"codex", "antigravity", "gemini"}

# Dedup precedence: earlier entries win when the same skill id appears in
# multiple layers.  custom (user-authored) beats external (imported repos).
LAYER_PRECEDENCE = [
    "custom",        # user-authored / customised skills
    "shared",        # team / org shared skills
    "codex",         # agent-specific
    "gemini",        # agent-specific
    "antigravity",   # agent-specific
    "imported",      # imported via skills.sh or similar
    "external",      # imported via scripts/import-skill.sh
]


def parse_skill_file(skill_md: Path, repo_root: Path) -> ToolRecord | None:
    """Parse a single SKILL.md into a ToolRecord.

    Returns None if the file cannot be parsed meaningfully.
    """
    try:
        if frontmatter is not None:
            post = frontmatter.load(str(skill_md))
            metadata = dict(post.metadata)
            content = str(post.content)
        else:
            raw = skill_md.read_text(encoding="utf-8", errors="ignore")
            metadata, content = _fallback_frontmatter_parse(raw)
            post = type("FrontmatterShim", (), {"metadata": metadata, "content": content})()
    except Exception:
        logger.warning("Failed to parse frontmatter: %s", skill_md)
        return None

    name = post.metadata.get("name", "")
    description = post.metadata.get("description", "")

    # Fallback: derive name from directory name
    if not name:
        name = skill_md.parent.name

    # Fallback: use first non-empty line of markdown body
    if not description:
        for line in post.content.splitlines():
            stripped = line.strip().lstrip("#").strip()
            if stripped:
                description = stripped[:200]
                break

    if not name:
        logger.debug("Skipping skill with no identifiable name: %s", skill_md)
        return None

    # Determine layer from path structure
    rel = skill_md.relative_to(repo_root / "skills")
    layer = rel.parts[0] if rel.parts else "unknown"
    source_repo, domain = infer_source_repo_and_domain(rel)
    skill_name = skill_md.parent.name
    source_path = skill_md.relative_to(repo_root).as_posix()

    tags = [f"layer:{layer}", f"skill:{skill_name}"]
    enabled_targets: list[str] = []
    if layer in TARGET_LAYERS:
        normalized_target = normalize_target(layer)
        if normalized_target:
            enabled_targets.append(normalized_target)
            tags.append(f"target:{normalized_target}")

    return ToolRecord(
        id=f"skill:{name}",
        name=name,
        description=description,
        tool_kind="skill",
        source_path=source_path,
        metadata={
            "layer": layer,
            "source_repo": source_repo,
            "domain": domain,
            "catalog_only": False,
            "executable": True,
            "has_frontmatter": bool(metadata),
            "body_length": len(content),
            "skill_name": skill_name,
            "enabled_targets": enabled_targets,
        },
        invoke={
            "backend": "skill_markdown",
            "command": source_path,
            "args": [],
            "timeout_ms": 10000,
            "env_keys": [],
        },
        tags=tags,
    )


def _fallback_frontmatter_parse(raw: str) -> tuple[dict[str, str], str]:
    metadata: dict[str, str] = {}
    content = raw
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) == 3:
            fm_body = parts[1]
            content = parts[2]
            for line in fm_body.splitlines():
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata, content


def scan_skills(repo_root: Path) -> list[ToolRecord]:
    """Recursively scan skills/ for SKILL.md files and parse them all.

    Scans layers in LAYER_PRECEDENCE order so that higher-priority layers
    (e.g. custom) win dedup over lower-priority layers (e.g. external)
    when two skills share the same id.
    """
    skills_dir = repo_root / "skills"
    if not skills_dir.is_dir():
        logger.warning("skills/ directory not found at %s", skills_dir)
        return []

    # Build ordered list of SKILL.md paths: precedence layers first, then rest.
    ordered_paths: list[Path] = []
    seen_paths: set[Path] = set()

    for layer in LAYER_PRECEDENCE:
        layer_dir = skills_dir / layer
        if layer_dir.is_dir():
            for p in sorted(layer_dir.rglob("SKILL.md")):
                if p not in seen_paths:
                    ordered_paths.append(p)
                    seen_paths.add(p)

    # Catch any layers not in LAYER_PRECEDENCE (future-proofing).
    for p in sorted(skills_dir.rglob("SKILL.md")):
        if p not in seen_paths:
            ordered_paths.append(p)
            seen_paths.add(p)

    records: list[ToolRecord] = []
    seen_ids: set[str] = set()

    for skill_md in ordered_paths:
        record = parse_skill_file(skill_md, repo_root)
        if record is None:
            continue

        # Deduplicate by id (first occurrence wins — guaranteed by layer order)
        if record.id in seen_ids:
            logger.debug("Duplicate skill id %s, skipping %s (lower precedence)", record.id, skill_md)
            continue

        seen_ids.add(record.id)
        records.append(record)

    logger.info("Parsed %d skills from %s", len(records), skills_dir)
    return records
