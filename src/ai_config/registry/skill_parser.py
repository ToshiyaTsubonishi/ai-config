"""Parser for SKILL.md files under skills/ directories.

Walks the skills tree, extracts YAML frontmatter (name, description) and
markdown body, and produces ToolRecord instances.
"""

from __future__ import annotations

import logging
from pathlib import Path

import frontmatter

from ai_config.registry.models import ToolRecord

logger = logging.getLogger(__name__)

# Skill layers expected at skills/<layer>/<skill-name>/SKILL.md
SKILL_LAYERS = ("shared", "external", "codex", "antigravity", "gemini")


def parse_skill_file(skill_md: Path, repo_root: Path) -> ToolRecord | None:
    """Parse a single SKILL.md into a ToolRecord.

    Returns None if the file cannot be parsed meaningfully.
    """
    try:
        post = frontmatter.load(str(skill_md))
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

    return ToolRecord(
        id=f"skill:{name}",
        name=name,
        description=description,
        tool_type="skill",
        source_path=str(skill_md.relative_to(repo_root)),
        metadata={
            "layer": layer,
            "has_frontmatter": bool(post.metadata),
            "body_length": len(post.content),
        },
    )


def scan_skills(repo_root: Path) -> list[ToolRecord]:
    """Recursively scan skills/ for SKILL.md files and parse them all."""
    skills_dir = repo_root / "skills"
    if not skills_dir.is_dir():
        logger.warning("skills/ directory not found at %s", skills_dir)
        return []

    records: list[ToolRecord] = []
    seen_ids: set[str] = set()

    for skill_md in sorted(skills_dir.rglob("SKILL.md")):
        record = parse_skill_file(skill_md, repo_root)
        if record is None:
            continue

        # Deduplicate by id (first occurrence wins)
        if record.id in seen_ids:
            logger.debug("Duplicate skill id %s, skipping %s", record.id, skill_md)
            continue

        seen_ids.add(record.id)
        records.append(record)

    logger.info("Parsed %d skills from %s", len(records), skills_dir)
    return records
