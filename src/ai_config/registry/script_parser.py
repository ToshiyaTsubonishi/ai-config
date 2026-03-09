"""Parser for executable scripts bundled under skills/**/scripts/**."""

from __future__ import annotations

import ast
import logging
import re
from pathlib import Path

from ai_config.registry.path_metadata import infer_source_repo_and_domain
from ai_config.registry.models import ToolRecord
from ai_config.registry.normalization import EXECUTION_TARGETS, normalize_target

logger = logging.getLogger(__name__)

SCRIPT_EXTENSIONS = {".py", ".ps1", ".sh", ".bash", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx"}
EXCLUDED_EXTENSIONS = {
    ".xsd",
    ".xml",
    ".json",
    ".yaml",
    ".yml",
    ".lock",
    ".gz",
    ".zip",
    ".png",
    ".jpg",
    ".jpeg",
    ".pdf",
    ".bin",
    ".exe",
    ".dll",
}
MAX_SCRIPT_BYTES = 512 * 1024


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _first_sentence(text: str, fallback: str) -> str:
    line = text.strip().splitlines()[0].strip() if text.strip() else ""
    if not line:
        return fallback
    return line[:300]


def _extract_python_doc(text: str, fallback: str) -> str:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return fallback

    module_doc = ast.get_docstring(tree)
    if module_doc:
        return _first_sentence(module_doc, fallback)

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            doc = ast.get_docstring(node)
            if doc:
                return _first_sentence(doc, fallback)

    return fallback


def _extract_ps1_doc(text: str, fallback: str) -> str:
    block = re.search(r"<#(.*?)#>", text, flags=re.DOTALL)
    if block:
        cleaned = re.sub(r"^[ \t]*\.[A-Za-z]+\s*", "", block.group(1), flags=re.MULTILINE)
        return _first_sentence(cleaned, fallback)
    return fallback


def _extract_shell_doc(text: str, fallback: str) -> str:
    lines = text.splitlines()
    comments: list[str] = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if i == 0 and stripped.startswith("#!"):
            continue
        if stripped.startswith("#"):
            comments.append(stripped.lstrip("#").strip())
            continue
        if comments:
            break
        if stripped:
            break
    return _first_sentence("\n".join(comments), fallback) if comments else fallback


def _extract_jsdoc(text: str, fallback: str) -> str:
    match = re.search(r"/\*\*(.*?)\*/", text, flags=re.DOTALL)
    if not match:
        return fallback

    raw = match.group(1)
    cleaned_lines = []
    for line in raw.splitlines():
        cleaned_lines.append(re.sub(r"^\s*\*\s?", "", line).strip())
    return _first_sentence("\n".join(cleaned_lines), fallback)


def _extract_description(path: Path, text: str) -> str:
    fallback = f"Script helper: {path.name}"
    suffix = path.suffix.lower()
    if suffix == ".py":
        return _extract_python_doc(text, fallback)
    if suffix == ".ps1":
        return _extract_ps1_doc(text, fallback)
    if suffix in {".sh", ".bash"}:
        return _extract_shell_doc(text, fallback)
    if suffix in {".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx"}:
        return _extract_jsdoc(text, fallback)
    return fallback


def _infer_layer_and_skill(rel_path: Path) -> tuple[str, str]:
    parts = rel_path.parts
    # rel_path shape starts after skills/.
    layer = parts[0] if parts else "unknown"
    skill_name = rel_path.parent.name
    if "scripts" in parts:
        idx = parts.index("scripts")
        if idx > 0:
            skill_name = parts[idx - 1]
    return layer, skill_name


def parse_script_file(script_path: Path, repo_root: Path) -> ToolRecord | None:
    """Parse a script file under skills tree into ToolRecord."""
    suffix = script_path.suffix.lower()
    if suffix not in SCRIPT_EXTENSIONS:
        return None
    if suffix in EXCLUDED_EXTENSIONS:
        return None
    if not script_path.is_file():
        return None

    try:
        size = script_path.stat().st_size
    except OSError:
        return None
    if size > MAX_SCRIPT_BYTES:
        return None

    rel = script_path.relative_to(repo_root)
    rel_posix = rel.as_posix()
    if "/scripts/" not in rel_posix:
        return None

    text = _read_text(script_path)
    description = _extract_description(script_path, text)

    rel_after_skills = script_path.relative_to(repo_root / "skills")
    layer, skill_name = _infer_layer_and_skill(rel_after_skills)
    source_repo, domain = infer_source_repo_and_domain(rel_after_skills)

    tags = [
        f"layer:{layer}",
        f"skill:{skill_name}",
        f"extension:{suffix.lstrip('.')}",
    ]

    enabled_targets: list[str] = []
    if layer in EXECUTION_TARGETS:
        normalized_target = normalize_target(layer)
        if normalized_target:
            enabled_targets.append(normalized_target)
            tags.append(f"target:{normalized_target}")

    record_id = f"skill_script:{rel_posix}"
    return ToolRecord(
        id=record_id,
        name=f"{skill_name}/{script_path.name}",
        description=description,
        source_path=rel_posix,
        tool_kind="skill_script",
        metadata={
            "layer": layer,
            "source_repo": source_repo,
            "domain": domain,
            "catalog_only": False,
            "executable": True,
            "skill_name": skill_name,
            "script_extension": suffix,
            "enabled_targets": enabled_targets,
        },
        invoke={
            "backend": "skill_script",
            "command": rel_posix,
            "args": [],
            "timeout_ms": 30000,
            "env_keys": [],
        },
        tags=tags,
    )


def scan_skill_scripts(repo_root: Path) -> list[ToolRecord]:
    """Scan scripts under the skills tree and parse executable metadata."""
    skills_dir = repo_root / "skills"
    if not skills_dir.is_dir():
        logger.warning("skills/ directory not found at %s", skills_dir)
        return []

    records: list[ToolRecord] = []
    seen_ids: set[str] = set()

    for script_path in sorted(skills_dir.rglob("*")):
        if not script_path.is_file():
            continue

        record = parse_script_file(script_path, repo_root)
        if record is None:
            continue
        if record.id in seen_ids:
            continue
        seen_ids.add(record.id)
        records.append(record)

    logger.info("Parsed %d skill scripts from %s", len(records), skills_dir)
    return records
