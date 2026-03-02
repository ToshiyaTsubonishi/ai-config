"""Source Manager: sync external skill/MCP repositories as git submodules.

Reads config/sources.yaml and ensures each declared source is present as a
git submodule under the repository root.  Supports add / update / remove /
list operations.
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

DEFAULT_MANIFEST = "config/sources.yaml"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class SourceEntry:
    """A single external source declaration."""

    name: str
    source_type: str  # "skill" | "mcp"
    url: str
    path: str
    branch: str = "main"


@dataclass
class SourceManifest:
    """Parsed sources.yaml content."""

    version: str = "1.0.0"
    sources: list[SourceEntry] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Manifest I/O
# ---------------------------------------------------------------------------

def load_manifest(repo_root: Path, manifest_rel: str = DEFAULT_MANIFEST) -> SourceManifest:
    """Load and validate sources.yaml."""
    manifest_path = repo_root / manifest_rel
    if not manifest_path.exists():
        logger.warning("Manifest not found at %s – returning empty manifest.", manifest_path)
        return SourceManifest()

    raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    entries: list[SourceEntry] = []
    for name, cfg in (raw.get("sources") or {}).items():
        entries.append(
            SourceEntry(
                name=name,
                source_type=cfg.get("type", "skill"),
                url=cfg["url"],
                path=cfg["path"],
                branch=cfg.get("branch", "main"),
            )
        )
    return SourceManifest(version=raw.get("version", "1.0.0"), sources=entries)


# ---------------------------------------------------------------------------
# Git submodule helpers
# ---------------------------------------------------------------------------

def _run_git(repo_root: Path, args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    cmd = ["git", "-C", str(repo_root), *args]
    logger.debug("Running: %s", " ".join(cmd))
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def _existing_submodule_paths(repo_root: Path) -> set[str]:
    """Return set of relative paths registered as git submodules."""
    proc = _run_git(repo_root, ["submodule", "status"], check=False)
    paths: set[str] = set()
    for line in (proc.stdout or "").splitlines():
        parts = line.strip().split()
        if len(parts) >= 2:
            # format: " <hash> <path> (<description>)"
            paths.add(parts[1])
    return paths


def _add_submodule(repo_root: Path, entry: SourceEntry) -> bool:
    """Add a new git submodule. Returns True on success."""
    logger.info("Adding submodule: %s → %s", entry.url, entry.path)
    proc = _run_git(
        repo_root,
        ["submodule", "add", "--branch", entry.branch, entry.url, entry.path],
        check=False,
    )
    if proc.returncode != 0:
        logger.error("Failed to add submodule %s: %s", entry.name, proc.stderr.strip())
        return False
    return True


def _update_submodule(repo_root: Path, entry: SourceEntry) -> bool:
    """Update an existing submodule to latest. Returns True on success."""
    logger.info("Updating submodule: %s", entry.path)
    proc = _run_git(
        repo_root,
        ["submodule", "update", "--remote", "--merge", "--", entry.path],
        check=False,
    )
    if proc.returncode != 0:
        logger.error("Failed to update submodule %s: %s", entry.name, proc.stderr.strip())
        return False
    return True


def _remove_submodule(repo_root: Path, path: str) -> bool:
    """Remove a git submodule that is no longer declared. Returns True on success."""
    logger.info("Removing submodule: %s", path)
    _run_git(repo_root, ["submodule", "deinit", "-f", "--", path], check=False)
    _run_git(repo_root, ["rm", "-f", path], check=False)

    git_modules_dir = repo_root / ".git" / "modules" / path
    if git_modules_dir.exists():
        import shutil
        shutil.rmtree(git_modules_dir, ignore_errors=True)
    return True


# ---------------------------------------------------------------------------
# High-level operations
# ---------------------------------------------------------------------------

def sync_sources(repo_root: Path, manifest_rel: str = DEFAULT_MANIFEST, *, dry_run: bool = False) -> dict[str, list[str]]:
    """Synchronize declared sources with actual git submodules.

    Returns a summary dict with keys: added, updated, removed, errors.
    """
    manifest = load_manifest(repo_root, manifest_rel)
    existing = _existing_submodule_paths(repo_root)
    declared_paths = {e.path for e in manifest.sources}

    result: dict[str, list[str]] = {"added": [], "updated": [], "removed": [], "errors": []}

    # Add or update declared sources
    for entry in manifest.sources:
        if entry.path in existing:
            if dry_run:
                logger.info("[DRY RUN] Would update: %s", entry.path)
                result["updated"].append(entry.path)
            else:
                if _update_submodule(repo_root, entry):
                    result["updated"].append(entry.path)
                else:
                    result["errors"].append(entry.path)
        else:
            if dry_run:
                logger.info("[DRY RUN] Would add: %s (%s)", entry.path, entry.url)
                result["added"].append(entry.path)
            else:
                if _add_submodule(repo_root, entry):
                    result["added"].append(entry.path)
                else:
                    result["errors"].append(entry.path)

    # Remove submodules under managed prefixes that are no longer declared
    managed_prefixes = ("skills/external/", "mcp/external/")
    for sub_path in existing:
        if any(sub_path.startswith(p) for p in managed_prefixes) and sub_path not in declared_paths:
            if dry_run:
                logger.info("[DRY RUN] Would remove: %s", sub_path)
                result["removed"].append(sub_path)
            else:
                if _remove_submodule(repo_root, sub_path):
                    result["removed"].append(sub_path)
                else:
                    result["errors"].append(sub_path)

    return result


def list_sources(repo_root: Path, manifest_rel: str = DEFAULT_MANIFEST) -> list[dict[str, str]]:
    """List all declared sources with their sync status."""
    manifest = load_manifest(repo_root, manifest_rel)
    existing = _existing_submodule_paths(repo_root)

    rows: list[dict[str, str]] = []
    for entry in manifest.sources:
        rows.append({
            "name": entry.name,
            "type": entry.source_type,
            "url": entry.url,
            "path": entry.path,
            "branch": entry.branch,
            "status": "synced" if entry.path in existing else "pending",
        })
    return rows


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    parser = argparse.ArgumentParser(description="Manage external skill/MCP sources.")
    parser.add_argument("--repo-root", type=Path, default=Path("."), help="Repository root path")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST, help="Manifest file relative path")
    sub = parser.add_subparsers(dest="command", required=True)

    sync_p = sub.add_parser("sync", help="Sync all declared sources (add/update/remove submodules)")
    sync_p.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")

    sub.add_parser("list", help="List all declared sources and their status")

    add_p = sub.add_parser("add", help="Add a new source to the manifest")
    add_p.add_argument("name", help="Source name (e.g. 'my-skills')")
    add_p.add_argument("url", help="Git repository URL")
    add_p.add_argument("--type", choices=("skill", "mcp"), default="skill", help="Source type")
    add_p.add_argument("--path", help="Local path (default: skills/external/<name> or mcp/external/<name>)")
    add_p.add_argument("--branch", default="main", help="Branch to track")

    rm_p = sub.add_parser("remove", help="Remove a source from the manifest")
    rm_p.add_argument("name", help="Source name to remove")

    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()

    if args.command == "sync":
        result = sync_sources(repo_root, args.manifest, dry_run=args.dry_run)
        print(f"Added:   {result['added']}")
        print(f"Updated: {result['updated']}")
        print(f"Removed: {result['removed']}")
        if result["errors"]:
            print(f"Errors:  {result['errors']}")
            sys.exit(1)

    elif args.command == "list":
        rows = list_sources(repo_root, args.manifest)
        if not rows:
            print("No sources declared.")
            return
        print(f"{'Name':<20} {'Type':<8} {'Status':<10} {'Path'}")
        print("-" * 70)
        for r in rows:
            print(f"{r['name']:<20} {r['type']:<8} {r['status']:<10} {r['path']}")

    elif args.command == "add":
        manifest_path = repo_root / args.manifest
        raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"version": "1.0.0", "sources": {}}
        if raw.get("sources") is None:
            raw["sources"] = {}

        default_prefix = "skills/external" if args.type == "skill" else "mcp/external"
        path = args.path or f"{default_prefix}/{args.name}"

        raw["sources"][args.name] = {
            "type": args.type,
            "url": args.url,
            "path": path,
            "branch": args.branch,
        }
        manifest_path.write_text(yaml.dump(raw, default_flow_style=False, allow_unicode=True), encoding="utf-8")
        print(f"Added source '{args.name}' to {args.manifest}")
        print(f"Run 'ai-config-sources sync' to clone the repository.")

    elif args.command == "remove":
        manifest_path = repo_root / args.manifest
        if not manifest_path.exists():
            print("Manifest not found.")
            sys.exit(1)
        raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        sources = raw.get("sources", {})
        if args.name not in sources:
            print(f"Source '{args.name}' not found in manifest.")
            sys.exit(1)
        del sources[args.name]
        manifest_path.write_text(yaml.dump(raw, default_flow_style=False, allow_unicode=True), encoding="utf-8")
        print(f"Removed source '{args.name}' from manifest.")
        print(f"Run 'ai-config-sources sync' to clean up the submodule.")


if __name__ == "__main__":
    main()
