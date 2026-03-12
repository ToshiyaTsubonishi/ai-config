"""Canonical vendor-layer implementation for repo-managed external skills."""

from __future__ import annotations

import configparser
import logging
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from ai_config.vendor.models import (
    LegacyBootstrapResult,
    PROVENANCE_FILENAME,
    PROVENANCE_SCHEMA_VERSION,
    VendorImportResult,
    VendorImportSpec,
    VendorProvenance,
)

logger = logging.getLogger(__name__)

_GITHUB_REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_GIT_URL_PREFIXES = ("https://", "http://", "git@", "ssh://", "file://")
_LEGACY_IMPORT_TOOL = "ai-config-vendor-skills bootstrap-legacy"
_IMPORT_TOOL = "ai-config-vendor-skills import"


class VendorError(RuntimeError):
    """Raised when vendor-layer operations cannot proceed safely."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _run_git(args: list[str], *, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    cmd = ["git", *args]
    logger.debug("Running: %s (cwd=%s)", " ".join(cmd), cwd)
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=check)


def _external_dir(repo_root: Path) -> Path:
    return repo_root / "skills" / "external"


def _provenance_path(target_dir: Path) -> Path:
    return target_dir / PROVENANCE_FILENAME


def _normalize_source(source: str) -> str:
    raw = source.strip()
    if not raw:
        raise VendorError("Source must not be empty.")
    if raw.startswith(_GIT_URL_PREFIXES):
        return raw

    possible_path = Path(raw).expanduser()
    if possible_path.exists():
        return str(possible_path.resolve())

    if _GITHUB_REPO_PATTERN.fullmatch(raw):
        return f"https://github.com/{raw}.git"

    raise VendorError(f"Cannot parse source: {source}")


def _derive_local_name(source: str) -> str:
    trimmed = source.rstrip("/").split("/")[-1]
    if trimmed.endswith(".git"):
        trimmed = trimmed[:-4]
    if trimmed:
        return trimmed
    raise VendorError(f"Cannot derive local name from source: {source}")


def _find_skill_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("SKILL.md") if ".git" not in path.parts)


def _remove_path(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
        return
    path.unlink()


def _sync_directory(src_dir: Path, dest_dir: Path, *, preserve_names: set[str] | None = None) -> None:
    preserve_names = preserve_names or set()
    dest_dir.mkdir(parents=True, exist_ok=True)

    source_names: set[str] = set()
    for child in src_dir.iterdir():
        if child.name == ".git":
            continue
        source_names.add(child.name)
        target = dest_dir / child.name
        _remove_path(target)
        if child.is_dir():
            shutil.copytree(child, target, ignore=shutil.ignore_patterns(".git"))
        else:
            shutil.copy2(child, target)

    for child in list(dest_dir.iterdir()):
        if child.name in preserve_names or child.name in source_names:
            continue
        _remove_path(child)


def _remove_orphaned_dirs(target_dir: Path, imported_dirs: list[str]) -> list[str]:
    expected = set(imported_dirs)
    removed: list[str] = []
    for child in sorted(target_dir.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        if child.name in expected:
            continue
        _remove_path(child)
        removed.append(child.name)
    return removed


def _collect_provenance(
    *,
    source_url: str,
    branch: str,
    commit_sha: str,
    original_paths: list[str],
    imported_at: str,
    updated_at: str,
    local_name: str,
    import_tool: str,
) -> VendorProvenance:
    return VendorProvenance(
        schema_version=PROVENANCE_SCHEMA_VERSION,
        source_url=source_url,
        branch=branch,
        commit_sha=commit_sha,
        original_paths=original_paths,
        imported_at=imported_at,
        updated_at=updated_at,
        import_tool=import_tool,
        skill_count=len(original_paths),
        local_name=local_name,
    )


def _clone_source(source: str, *, branch: str | None) -> tuple[Path, str, str]:
    temp_dir = Path(tempfile.mkdtemp(prefix="ai-config-vendor-"))
    clone_dir = temp_dir / "repo"
    clone_args = ["clone", "--depth", "1", "--quiet"]
    if branch:
        clone_args.extend(["--branch", branch])
    clone_args.extend([source, str(clone_dir)])
    try:
        _run_git(clone_args, cwd=temp_dir)
        commit_sha = _run_git(["rev-parse", "HEAD"], cwd=clone_dir).stdout.strip()
        clone_branch = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=clone_dir).stdout.strip()
        if clone_branch == "HEAD":
            clone_branch = branch or ""
        return clone_dir, commit_sha, clone_branch
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def _cleanup_clone(clone_dir: Path) -> None:
    shutil.rmtree(clone_dir.parent, ignore_errors=True)


def _existing_provenance(target_dir: Path) -> VendorProvenance | None:
    provenance_path = _provenance_path(target_dir)
    if not provenance_path.exists():
        return None
    return VendorProvenance.from_path(provenance_path)


def import_skill_repo(spec: VendorImportSpec, *, repo_root: Path) -> VendorImportResult:
    repo_root = repo_root.resolve()
    external_dir = _external_dir(repo_root)
    external_dir.mkdir(parents=True, exist_ok=True)

    normalized_source = _normalize_source(spec.source_url)
    local_name = spec.local_name or _derive_local_name(normalized_source)
    target_dir = external_dir / local_name
    old_provenance = _existing_provenance(target_dir)

    clone_dir, commit_sha, clone_branch = _clone_source(normalized_source, branch=spec.branch)
    try:
        import_ts = _utc_now()
        if old_provenance and old_provenance.commit_sha == commit_sha and not spec.force:
            return VendorImportResult(
                local_name=local_name,
                status="up_to_date",
                skill_count=old_provenance.skill_count,
                target_dir=str(target_dir.relative_to(repo_root)),
                provenance_path=str(_provenance_path(target_dir).relative_to(repo_root)),
                message=f"Already up to date (SHA: {commit_sha[:12]}). Use --force to re-import.",
            )

        skill_files = _find_skill_files(clone_dir)
        original_paths = [str(path.relative_to(clone_dir).as_posix()) for path in skill_files]
        if not skill_files:
            raise VendorError(f"No SKILL.md files found in {spec.source_url}")

        if spec.dry_run:
            return VendorImportResult(
                local_name=local_name,
                status="dry_run",
                skill_count=len(skill_files),
                target_dir=str(target_dir.relative_to(repo_root)),
                provenance_path=str(_provenance_path(target_dir).relative_to(repo_root)),
                message=f"Would import {len(skill_files)} skill(s).",
            )

        target_dir.mkdir(parents=True, exist_ok=True)
        imported_dirs: list[str] = []
        for skill_file in skill_files:
            skill_dir = skill_file.parent
            if skill_dir == clone_dir:
                dest_dir = target_dir
                preserve_names = {PROVENANCE_FILENAME}
            else:
                dest_dir = target_dir / skill_dir.name
                imported_dirs.append(skill_dir.name)
                preserve_names = set()
            _sync_directory(skill_dir, dest_dir, preserve_names=preserve_names)

        orphaned_dirs: list[str] = []
        if imported_dirs:
            orphaned_dirs = _remove_orphaned_dirs(target_dir, imported_dirs)

        provenance = _collect_provenance(
            source_url=normalized_source,
            branch=clone_branch or (spec.branch or ""),
            commit_sha=commit_sha,
            original_paths=original_paths,
            imported_at=old_provenance.imported_at if old_provenance and old_provenance.imported_at else import_ts,
            updated_at=import_ts,
            local_name=local_name,
            import_tool=_IMPORT_TOOL,
        )
        provenance.write(_provenance_path(target_dir))

        return VendorImportResult(
            local_name=local_name,
            status="imported" if old_provenance is None else "updated",
            skill_count=len(skill_files),
            target_dir=str(target_dir.relative_to(repo_root)),
            provenance_path=str(_provenance_path(target_dir).relative_to(repo_root)),
            orphaned_dirs=orphaned_dirs,
            message=f"Imported {len(skill_files)} skill(s).",
        )
    finally:
        _cleanup_clone(clone_dir)


def _iter_provenance_files(repo_root: Path) -> list[Path]:
    external_dir = _external_dir(repo_root)
    if not external_dir.is_dir():
        return []
    return sorted(path for path in external_dir.glob(f"*/{PROVENANCE_FILENAME}") if path.is_file())


def update_imported_skills(
    *,
    repo_root: Path,
    local_name: str | None = None,
    update_all: bool = False,
    force: bool = False,
    dry_run: bool = False,
) -> list[VendorImportResult]:
    repo_root = repo_root.resolve()
    provenance_files: list[Path]

    if local_name:
        provenance_path = _provenance_path(_external_dir(repo_root) / local_name)
        provenance_files = [provenance_path] if provenance_path.exists() else []
    elif update_all:
        provenance_files = _iter_provenance_files(repo_root)
    else:
        raise VendorError("Specify a local name or use --all.")

    if not provenance_files:
        raise VendorError(
            "No provenance files found. Run bootstrap-legacy for existing checkouts before update."
        )

    results: list[VendorImportResult] = []
    for provenance_path in provenance_files:
        provenance = VendorProvenance.from_path(provenance_path)
        results.append(
            import_skill_repo(
                VendorImportSpec(
                    source_url=provenance.source_url,
                    local_name=provenance.local_name,
                    branch=provenance.branch or None,
                    force=force,
                    dry_run=dry_run,
                ),
                repo_root=repo_root,
            )
        )
    return results


def remove_imported_skill(*, repo_root: Path, local_name: str, dry_run: bool = False) -> VendorImportResult:
    repo_root = repo_root.resolve()
    target_dir = _external_dir(repo_root) / local_name
    if not target_dir.exists():
        return VendorImportResult(
            local_name=local_name,
            status="missing",
            target_dir=str(target_dir.relative_to(repo_root)),
            provenance_path=str(_provenance_path(target_dir).relative_to(repo_root)),
            message="Target directory does not exist.",
        )

    skill_count = len(_find_skill_files(target_dir))
    if dry_run:
        return VendorImportResult(
            local_name=local_name,
            status="dry_run",
            skill_count=skill_count,
            target_dir=str(target_dir.relative_to(repo_root)),
            provenance_path=str(_provenance_path(target_dir).relative_to(repo_root)),
            message="Would remove imported skill directory.",
        )

    _remove_path(target_dir)
    return VendorImportResult(
        local_name=local_name,
        status="removed",
        skill_count=skill_count,
        target_dir=str(target_dir.relative_to(repo_root)),
        provenance_path=str(_provenance_path(target_dir).relative_to(repo_root)),
        message="Removed imported skill directory.",
    )


def _read_gitmodules(repo_root: Path) -> dict[str, dict[str, str]]:
    gitmodules_path = repo_root / ".gitmodules"
    if not gitmodules_path.exists():
        return {}

    parser = configparser.ConfigParser()
    parser.read(gitmodules_path, encoding="utf-8")
    result: dict[str, dict[str, str]] = {}
    for section in parser.sections():
        if not section.startswith("submodule "):
            continue
        path = parser.get(section, "path", fallback="")
        if not path:
            continue
        result[path] = {
            "url": parser.get(section, "url", fallback=""),
            "branch": parser.get(section, "branch", fallback=""),
        }
    return result


def _git_output(args: list[str], *, cwd: Path) -> str:
    proc = _run_git(args, cwd=cwd, check=False)
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def bootstrap_legacy_imports(
    *,
    repo_root: Path,
    local_name: str | None = None,
    bootstrap_all: bool = False,
    dry_run: bool = False,
) -> list[LegacyBootstrapResult]:
    """Backfill provenance for existing legacy checkouts.

    This is a migration utility for Phase 1. It is not intended to be a
    permanent day-to-day workflow surface.
    """

    repo_root = repo_root.resolve()
    external_dir = _external_dir(repo_root)
    external_dir.mkdir(parents=True, exist_ok=True)

    if local_name:
        candidates = [external_dir / local_name]
    elif bootstrap_all:
        candidates = sorted(path for path in external_dir.iterdir() if path.is_dir())
    else:
        raise VendorError("Specify a local name or use --all.")

    gitmodules = _read_gitmodules(repo_root)
    results: list[LegacyBootstrapResult] = []
    timestamp = _utc_now()

    for target_dir in candidates:
        local = target_dir.name
        provenance_path = _provenance_path(target_dir)
        rel_target = str(target_dir.relative_to(repo_root))
        rel_provenance = str(provenance_path.relative_to(repo_root))

        if not target_dir.exists():
            results.append(
                LegacyBootstrapResult(
                    local_name=local,
                    status="missing",
                    target_dir=rel_target,
                    provenance_path=rel_provenance,
                    message="Target directory does not exist.",
                )
            )
            continue

        if provenance_path.exists():
            existing = VendorProvenance.from_path(provenance_path)
            results.append(
                LegacyBootstrapResult(
                    local_name=local,
                    status="already_bootstrapped",
                    skill_count=existing.skill_count,
                    target_dir=rel_target,
                    provenance_path=rel_provenance,
                    source_url=existing.source_url,
                    message="Provenance already exists.",
                )
            )
            continue

        rel_path = rel_target
        source_url = gitmodules.get(rel_path, {}).get("url", "")
        branch = gitmodules.get(rel_path, {}).get("branch", "")
        if not source_url:
            source_url = _git_output(["remote", "get-url", "origin"], cwd=target_dir)
        if not branch:
            branch = _git_output(["rev-parse", "--abbrev-ref", "HEAD"], cwd=target_dir)
        if branch == "HEAD":
            branch = ""

        commit_sha = _git_output(["rev-parse", "HEAD"], cwd=target_dir)
        skill_files = _find_skill_files(target_dir)
        if not source_url or not commit_sha or not skill_files:
            results.append(
                LegacyBootstrapResult(
                    local_name=local,
                    status="skipped",
                    skill_count=len(skill_files),
                    target_dir=rel_target,
                    provenance_path=rel_provenance,
                    source_url=source_url,
                    message="Could not determine source metadata or no SKILL.md files were found.",
                )
            )
            continue

        original_paths = [str(path.relative_to(target_dir).as_posix()) for path in skill_files]
        provenance = _collect_provenance(
            source_url=source_url,
            branch=branch,
            commit_sha=commit_sha,
            original_paths=original_paths,
            imported_at=timestamp,
            updated_at=timestamp,
            local_name=local,
            import_tool=_LEGACY_IMPORT_TOOL,
        )

        if not dry_run:
            provenance.write(provenance_path)

        results.append(
            LegacyBootstrapResult(
                local_name=local,
                status="dry_run" if dry_run else "bootstrapped",
                skill_count=len(original_paths),
                target_dir=rel_target,
                provenance_path=rel_provenance,
                source_url=source_url,
                message="Would backfill provenance for legacy checkout."
                if dry_run
                else "Backfilled provenance for legacy checkout.",
            )
        )

    return results
