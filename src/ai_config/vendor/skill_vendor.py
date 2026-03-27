"""Canonical vendor-layer implementation for repo-managed external skills."""

from __future__ import annotations

import configparser
import logging
import os
import re
import stat
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

from ai_config.vendor.models import (
    DEFAULT_EXTERNAL_TARGET_ROOT,
    DEFAULT_OFFICIAL_TARGET_ROOT,
    DEFAULT_SKILLS_SH_OFFICIAL_MANIFEST,
    DEFAULT_VENDOR_MANIFEST,
    LegacyBootstrapResult,
    LegacyCleanupResult,
    PROVENANCE_FILENAME,
    PROVENANCE_SCHEMA_VERSION,
    VendorImportResult,
    VendorImportSpec,
    VendorManifest,
    VendorManifestEntry,
    VendorProvenance,
    VendorStatusEntry,
    VendorStatusReport,
    VendorStatusSummary,
    VENDOR_STATUS_SCHEMA_VERSION,
    VendorSyncResult,
)

logger = logging.getLogger(__name__)

_GITHUB_REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_GIT_URL_PREFIXES = ("https://", "http://", "git@", "ssh://", "file://")
_LEGACY_IMPORT_TOOL = "ai-config-vendor-skills bootstrap-legacy"
_IMPORT_TOOL = "ai-config-vendor-skills import"
_OFFICIAL_IMPORT_TOOL = "ai-config-vendor-skills sync-skills-sh-official"


class VendorError(RuntimeError):
    """Raised when vendor-layer operations cannot proceed safely."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _run_git(args: list[str], *, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    cmd = ["git", *args]
    logger.debug("Running: %s (cwd=%s)", " ".join(cmd), cwd)
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=check)


def _require_git_success(proc: subprocess.CompletedProcess[str], action: str) -> None:
    if proc.returncode == 0:
        return
    stderr = (proc.stderr or "").strip()
    stdout = (proc.stdout or "").strip()
    detail = stderr or stdout or "unknown git error"
    raise VendorError(f"{action} failed: {detail}")


def _target_root_dir(repo_root: Path, target_root_rel: str) -> Path:
    target_root = (repo_root / target_root_rel).resolve()
    try:
        target_root.relative_to(repo_root)
    except ValueError as error:  # pragma: no cover - defensive path guard
        raise VendorError(f"Target root must stay inside the repository: {target_root_rel}") from error
    return target_root


def _external_dir(repo_root: Path) -> Path:
    return _target_root_dir(repo_root, DEFAULT_EXTERNAL_TARGET_ROOT)


def _repo_rel(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


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
        def _onerror(func: object, target: str, exc_info: tuple[type[BaseException], BaseException, object]) -> None:
            if not isinstance(exc_info[1], PermissionError):
                raise exc_info[1]
            os.chmod(target, stat.S_IWRITE)
            func(target)

        shutil.rmtree(path, onerror=_onerror)
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
    requested_ref: str | None,
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
        requested_ref=requested_ref,
        commit_sha=commit_sha,
        original_paths=original_paths,
        imported_at=imported_at,
        updated_at=updated_at,
        import_tool=import_tool,
        skill_count=len(original_paths),
        local_name=local_name,
    )


def _clone_source(source: str, *, branch: str | None, ref: str | None) -> tuple[Path, str, str]:
    temp_dir = Path(tempfile.mkdtemp(prefix="ai-config-vendor-"))
    clone_dir = temp_dir / "repo"
    clone_args = ["clone", "--quiet"]
    if branch and not ref:
        clone_args.extend(["--branch", branch])
    clone_args.extend([source, str(clone_dir)])
    try:
        _run_git(clone_args, cwd=temp_dir)
        if ref:
            _run_git(["checkout", "--quiet", ref], cwd=clone_dir)
        elif branch:
            _run_git(["checkout", "--quiet", branch], cwd=clone_dir, check=False)
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


def _git_output(args: list[str], *, cwd: Path) -> str:
    proc = _run_git(args, cwd=cwd, check=False)
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def _local_git_commit(target_dir: Path) -> str:
    if not target_dir.exists():
        return ""
    return _git_output(["rev-parse", "HEAD"], cwd=target_dir)


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


def _is_git_submodule(repo_root: Path, rel_path: str) -> bool:
    proc = _run_git(["-C", str(repo_root), "ls-files", "--stage", "--", rel_path], cwd=repo_root, check=False)
    if proc.returncode != 0:
        return False
    for line in (proc.stdout or "").splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[0] == "160000":
            return True
    return False


def _is_git_ignored(repo_root: Path, rel_path: str) -> bool:
    git_dir = repo_root / ".git"
    if not git_dir.exists():
        return False
    proc = _run_git(["check-ignore", "-q", "--", rel_path], cwd=repo_root, check=False)
    return proc.returncode == 0


def _skill_count(target_dir: Path, provenance: VendorProvenance | None) -> int:
    if provenance is not None and provenance.skill_count:
        return provenance.skill_count
    if not target_dir.exists():
        return 0
    return len(_find_skill_files(target_dir))


def _build_status_summary(entries: list[VendorStatusEntry], *, total_manifest_entries: int) -> VendorStatusSummary:
    summary = VendorStatusSummary(total_manifest_entries=total_manifest_entries)
    known_statuses = {
        "ready",
        "needs_align",
        "needs_sync",
        "missing",
        "legacy_submodule",
        "missing_provenance",
        "extra_local",
        "unmanaged_local",
    }
    for entry in entries:
        if entry.status not in known_statuses:
            continue
        setattr(summary, entry.status, getattr(summary, entry.status) + 1)
    return summary


def _remove_gitmodules_entry(repo_root: Path, rel_path: str) -> bool:
    gitmodules_path = repo_root / ".gitmodules"
    if not gitmodules_path.exists():
        return False

    parser = configparser.ConfigParser()
    parser.read(gitmodules_path, encoding="utf-8")
    removed = False
    for section in list(parser.sections()):
        if parser.get(section, "path", fallback="") != rel_path:
            continue
        parser.remove_section(section)
        removed = True

    if not removed:
        return False

    if parser.sections():
        with gitmodules_path.open("w", encoding="utf-8") as handle:
            parser.write(handle)
    else:
        gitmodules_path.unlink()

    _run_git(["-C", str(repo_root), "add", "-A", "--", ".gitmodules"], cwd=repo_root, check=False)
    return True


def _write_aligned_provenance(
    *,
    repo_root: Path,
    target_dir: Path,
    existing: VendorProvenance,
    source_url: str,
    branch: str,
    requested_ref: str,
    dry_run: bool,
) -> VendorSyncResult:
    provenance_path = _provenance_path(target_dir)
    rel_target = target_dir.relative_to(repo_root).as_posix()
    rel_provenance = provenance_path.relative_to(repo_root).as_posix()
    if not dry_run:
        aligned = _collect_provenance(
            source_url=source_url,
            branch=branch,
            requested_ref=requested_ref,
            commit_sha=existing.commit_sha,
            original_paths=existing.original_paths,
            imported_at=existing.imported_at,
            updated_at=existing.updated_at,
            local_name=existing.local_name,
            import_tool=existing.import_tool,
        )
        aligned.write(provenance_path)
    return VendorSyncResult(
        local_name=target_dir.name,
        status="aligned" if not dry_run else "dry_run",
        target_dir=rel_target,
        provenance_path=rel_provenance,
        source_url=source_url,
        requested_ref=requested_ref,
        message=(
            "Would align provenance metadata with the manifest pin."
            if dry_run
            else "Aligned provenance metadata with the manifest pin."
        ),
    )


def _sync_result_from_import(repo_root: Path, result: VendorImportResult, *, source_url: str, requested_ref: str) -> VendorSyncResult:
    return VendorSyncResult(
        local_name=result.local_name,
        status=result.status,
        target_dir=result.target_dir,
        provenance_path=result.provenance_path,
        source_url=source_url,
        requested_ref=requested_ref,
        message=result.message,
    )


def import_skill_repo(spec: VendorImportSpec, *, repo_root: Path) -> VendorImportResult:
    repo_root = repo_root.resolve()
    target_root = _target_root_dir(repo_root, spec.target_root)
    target_root.mkdir(parents=True, exist_ok=True)

    normalized_source = _normalize_source(spec.source_url)
    local_name = spec.local_name or _derive_local_name(normalized_source)
    target_dir = target_root / local_name
    rel_target = _repo_rel(target_dir, repo_root)
    old_provenance = _existing_provenance(target_dir)

    if _is_git_submodule(repo_root, rel_target):
        raise VendorError(
            f"{rel_target} is still a legacy submodule. "
            "Run cleanup-legacy-submodule first instead of importing over the gitlink."
        )

    if target_dir.exists() and old_provenance is None and _local_git_commit(target_dir):
        raise VendorError(
            f"{rel_target} is a git checkout without provenance. "
            "Run bootstrap-legacy first if this is a legacy checkout."
        )

    clone_dir, commit_sha, clone_branch = _clone_source(normalized_source, branch=spec.branch, ref=spec.ref)
    try:
        import_ts = _utc_now()
        if (
            old_provenance
            and old_provenance.commit_sha == commit_sha
            and old_provenance.requested_ref == spec.ref
            and not spec.force
        ):
            return VendorImportResult(
                local_name=local_name,
                status="up_to_date",
                skill_count=old_provenance.skill_count,
                target_dir=_repo_rel(target_dir, repo_root),
                provenance_path=_repo_rel(_provenance_path(target_dir), repo_root),
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
                target_dir=_repo_rel(target_dir, repo_root),
                provenance_path=_repo_rel(_provenance_path(target_dir), repo_root),
                message=f"Would import {len(skill_files)} skill(s).",
            )

        target_dir.mkdir(parents=True, exist_ok=True)
        imported_dirs: set[str] = set()
        for skill_file in skill_files:
            skill_dir = skill_file.parent
            if skill_dir == clone_dir:
                dest_dir = target_dir
                preserve_names = {PROVENANCE_FILENAME}
            else:
                dest_dir = target_dir / skill_dir.name
                imported_dirs.add(skill_dir.name)
                preserve_names = set()
            _sync_directory(skill_dir, dest_dir, preserve_names=preserve_names)

        orphaned_dirs: list[str] = []
        if imported_dirs:
            orphaned_dirs = _remove_orphaned_dirs(target_dir, sorted(imported_dirs))

        provenance = _collect_provenance(
            source_url=normalized_source,
            branch=clone_branch or (spec.branch or ""),
            requested_ref=spec.ref,
            commit_sha=commit_sha,
            original_paths=original_paths,
            imported_at=old_provenance.imported_at if old_provenance and old_provenance.imported_at else import_ts,
            updated_at=import_ts,
            local_name=local_name,
            import_tool=spec.import_tool or _IMPORT_TOOL,
        )
        provenance.write(_provenance_path(target_dir))

        return VendorImportResult(
            local_name=local_name,
            status="imported" if old_provenance is None else "updated",
            skill_count=len(skill_files),
            target_dir=_repo_rel(target_dir, repo_root),
            provenance_path=_repo_rel(_provenance_path(target_dir), repo_root),
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
                    ref=provenance.requested_ref,
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
    rel_target = _repo_rel(target_dir, repo_root)
    if not target_dir.exists():
        return VendorImportResult(
            local_name=local_name,
            status="missing",
            target_dir=rel_target,
            provenance_path=_repo_rel(_provenance_path(target_dir), repo_root),
            message="Target directory does not exist.",
        )

    if _is_git_submodule(repo_root, rel_target):
        raise VendorError(
            f"{rel_target} is still a legacy submodule. "
            "Run cleanup-legacy-submodule before removing vendor-managed payload."
        )

    skill_count = len(_find_skill_files(target_dir))
    if dry_run:
        return VendorImportResult(
            local_name=local_name,
            status="dry_run",
            skill_count=skill_count,
            target_dir=rel_target,
            provenance_path=_repo_rel(_provenance_path(target_dir), repo_root),
            message="Would remove imported skill directory.",
        )

    _remove_path(target_dir)
    return VendorImportResult(
        local_name=local_name,
        status="removed",
        skill_count=skill_count,
        target_dir=rel_target,
        provenance_path=_repo_rel(_provenance_path(target_dir), repo_root),
        message="Removed imported skill directory.",
    )


def load_vendor_manifest(repo_root: Path, manifest_rel: str = DEFAULT_VENDOR_MANIFEST) -> VendorManifest:
    repo_root = repo_root.resolve()
    manifest_path = repo_root / manifest_rel
    if not manifest_path.exists():
        raise VendorError(f"Vendor manifest not found: {manifest_rel}")

    raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    sources_raw = raw.get("sources") or {}
    if not isinstance(sources_raw, dict):
        raise VendorError(f"Vendor manifest sources must be a mapping: {manifest_rel}")

    entries: list[VendorManifestEntry] = []
    for name, cfg in sources_raw.items():
        if not isinstance(cfg, dict):
            raise VendorError(f"Vendor manifest entry '{name}' must be a mapping.")
        source_url = str(cfg.get("source_url") or cfg.get("url") or "").strip()
        local_name = str(cfg.get("local_name") or name).strip()
        branch = str(cfg.get("branch") or "main").strip() or "main"
        ref = str(cfg.get("ref") or "").strip() or None
        if not source_url:
            raise VendorError(f"Vendor manifest entry '{name}' is missing source_url.")
        entries.append(
            VendorManifestEntry(
                name=str(name),
                source_url=source_url,
                local_name=local_name,
                branch=branch,
                ref=ref,
            )
        )
    return VendorManifest(version=str(raw.get("version", "1.0.0")), sources=entries)


def inspect_vendor_state(repo_root: Path, manifest_rel: str = DEFAULT_VENDOR_MANIFEST) -> VendorStatusReport:
    """Inspect vendor-managed external skills without mutating repo state."""

    repo_root = repo_root.resolve()
    manifest_path = repo_root / manifest_rel
    external_dir = _external_dir(repo_root)
    manifest_errors: list[str] = []

    try:
        manifest = load_vendor_manifest(repo_root, manifest_rel)
    except VendorError as error:
        manifest = VendorManifest()
        manifest_errors.append(str(error))

    local_name_counts: dict[str, int] = {}
    for entry in manifest.sources:
        local_name_counts[entry.local_name] = local_name_counts.get(entry.local_name, 0) + 1
    for local_name, count in sorted(local_name_counts.items()):
        if count > 1:
            manifest_errors.append(f"Duplicate local_name '{local_name}' appears {count} times in {manifest_rel}.")

    entries: list[VendorStatusEntry] = []
    managed_local_names = {entry.local_name for entry in manifest.sources}

    for entry in manifest.sources:
        target_dir = external_dir / entry.local_name
        provenance_path = _provenance_path(target_dir)
        rel_target = _repo_rel(target_dir, repo_root)
        rel_provenance = _repo_rel(provenance_path, repo_root)
        provenance = _existing_provenance(target_dir)
        target_exists = target_dir.exists()
        provenance_exists = provenance is not None
        is_git_submodule = _is_git_submodule(repo_root, rel_target)
        git_ignored = _is_git_ignored(repo_root, rel_target)

        if not entry.ref:
            manifest_errors.append(
                f"Vendor manifest entry '{entry.name}' ({entry.local_name}) is missing ref."
            )

        if is_git_submodule:
            status = "legacy_submodule"
            message = "Target is still registered as a legacy git submodule."
        elif not target_exists:
            status = "missing"
            message = "Target directory is missing; run sync-manifest to materialize it."
        elif not provenance_exists:
            status = "missing_provenance"
            message = "Target directory exists without provenance metadata."
        elif not entry.ref:
            status = "needs_sync"
            message = "Manifest entry is missing an exact ref; sync-manifest cannot verify reproducibility."
        elif provenance.commit_sha != entry.ref:
            status = "needs_sync"
            message = "Local payload does not match the pinned manifest ref."
        elif (
            provenance.requested_ref != entry.ref
            or provenance.source_url != entry.source_url
            or (entry.branch and provenance.branch != entry.branch)
        ):
            status = "needs_align"
            message = "Payload matches the pin, but provenance metadata is stale."
        else:
            status = "ready"
            message = "Vendor-managed payload matches the pinned manifest ref."

        entries.append(
            VendorStatusEntry(
                manifest_name=entry.name,
                local_name=entry.local_name,
                status=status,
                source_url=entry.source_url,
                branch=entry.branch,
                target_dir=rel_target,
                provenance_path=rel_provenance,
                manifest_ref=entry.ref,
                provenance_commit_sha=provenance.commit_sha if provenance else None,
                provenance_requested_ref=provenance.requested_ref if provenance else None,
                skill_count=_skill_count(target_dir, provenance),
                target_exists=target_exists,
                provenance_exists=provenance_exists,
                is_git_submodule=is_git_submodule,
                git_ignored=git_ignored,
                is_manifest_managed=True,
                message=message,
            )
        )

    if external_dir.is_dir():
        for target_dir in sorted(path for path in external_dir.iterdir() if path.is_dir() and not path.name.startswith(".")):
            if target_dir.name in managed_local_names:
                continue
            provenance = _existing_provenance(target_dir)
            rel_target = _repo_rel(target_dir, repo_root)
            rel_provenance = _repo_rel(_provenance_path(target_dir), repo_root)
            is_git_submodule = _is_git_submodule(repo_root, rel_target)
            git_ignored = _is_git_ignored(repo_root, rel_target)

            if is_git_submodule:
                status = "legacy_submodule"
                message = "Local external directory is still a legacy git submodule and is not in the manifest."
            elif provenance is not None:
                status = "extra_local"
                message = "Vendor-managed local payload exists outside the curated manifest."
            else:
                status = "unmanaged_local"
                message = "Local external content exists without manifest coverage or provenance metadata."

            entries.append(
                VendorStatusEntry(
                    manifest_name=None,
                    local_name=target_dir.name,
                    status=status,
                    source_url=provenance.source_url if provenance else "",
                    branch=provenance.branch if provenance else "",
                    target_dir=rel_target,
                    provenance_path=rel_provenance,
                    manifest_ref=None,
                    provenance_commit_sha=provenance.commit_sha if provenance else None,
                    provenance_requested_ref=provenance.requested_ref if provenance else None,
                    skill_count=_skill_count(target_dir, provenance),
                    target_exists=True,
                    provenance_exists=provenance is not None,
                    is_git_submodule=is_git_submodule,
                    git_ignored=git_ignored,
                    is_manifest_managed=False,
                    message=message,
                )
            )

    summary = _build_status_summary(entries, total_manifest_entries=len(manifest.sources))
    return VendorStatusReport(
        schema_version=VENDOR_STATUS_SCHEMA_VERSION,
        generated_at=_utc_now(),
        repo_root=str(repo_root),
        manifest_path=str(manifest_path),
        summary=summary,
        entries=entries,
        manifest_errors=manifest_errors,
    )


def sync_vendor_manifest(
    *,
    repo_root: Path,
    manifest_rel: str = DEFAULT_VENDOR_MANIFEST,
    target_root_rel: str = DEFAULT_EXTERNAL_TARGET_ROOT,
    import_tool: str = _IMPORT_TOOL,
    prune: bool = False,
    dry_run: bool = False,
) -> list[VendorSyncResult]:
    repo_root = repo_root.resolve()
    manifest = load_vendor_manifest(repo_root, manifest_rel)
    target_root = _target_root_dir(repo_root, target_root_rel)
    target_root.mkdir(parents=True, exist_ok=True)

    results: list[VendorSyncResult] = []
    manifest_local_names: set[str] = set()

    for entry in manifest.sources:
        if not entry.ref:
            raise VendorError(
                f"Vendor manifest entry '{entry.name}' must pin an exact ref. "
                "Pinned refs are required for reproducible setup."
            )

        normalized_source = _normalize_source(entry.source_url)
        target_dir = target_root / entry.local_name
        provenance_path = _provenance_path(target_dir)
        rel_target = _repo_rel(target_dir, repo_root)
        rel_provenance = _repo_rel(provenance_path, repo_root)
        manifest_local_names.add(entry.local_name)

        existing = _existing_provenance(target_dir)
        current_commit = _local_git_commit(target_dir)
        if existing and (existing.commit_sha == entry.ref or current_commit == entry.ref):
            if (
                existing.requested_ref != entry.ref
                or existing.source_url != normalized_source
                or (entry.branch and existing.branch != entry.branch)
            ):
                results.append(
                    _write_aligned_provenance(
                        repo_root=repo_root,
                        target_dir=target_dir,
                        existing=existing,
                        source_url=normalized_source,
                        branch=entry.branch,
                        requested_ref=entry.ref,
                        dry_run=dry_run,
                    )
                )
            else:
                results.append(
                    VendorSyncResult(
                        local_name=entry.local_name,
                        status="up_to_date",
                        target_dir=rel_target,
                        provenance_path=rel_provenance,
                        source_url=normalized_source,
                        requested_ref=entry.ref,
                        message=f"Already materialized at {entry.ref[:12]}.",
                    )
                )
            continue

        if target_dir.exists() and _is_git_submodule(repo_root, rel_target):
            results.append(
                VendorSyncResult(
                    local_name=entry.local_name,
                    status="blocked",
                    target_dir=rel_target,
                    provenance_path=rel_provenance,
                    source_url=normalized_source,
                    requested_ref=entry.ref,
                    message=(
                        "Target is still a legacy submodule. "
                        "Run bootstrap-legacy if needed, then cleanup-legacy-submodule before syncing."
                    ),
                )
            )
            continue

        if target_dir.exists() and existing is None:
            results.append(
                VendorSyncResult(
                    local_name=entry.local_name,
                    status="blocked",
                    target_dir=rel_target,
                    provenance_path=rel_provenance,
                    source_url=normalized_source,
                    requested_ref=entry.ref,
                    message="Target directory exists without provenance; refusing to overwrite unmanaged local content.",
                )
            )
            continue

        result = import_skill_repo(
            VendorImportSpec(
                source_url=normalized_source,
                local_name=entry.local_name,
                branch=entry.branch,
                ref=entry.ref,
                target_root=target_root_rel,
                import_tool=import_tool,
                dry_run=dry_run,
            ),
            repo_root=repo_root,
        )
        results.append(_sync_result_from_import(repo_root, result, source_url=normalized_source, requested_ref=entry.ref))

    if not prune:
        return results

    for target_dir in sorted(path for path in target_root.iterdir() if path.is_dir() and not path.name.startswith(".")):
        if target_dir.name in manifest_local_names:
            continue
        provenance = _existing_provenance(target_dir)
        rel_target = _repo_rel(target_dir, repo_root)
        rel_provenance = _repo_rel(_provenance_path(target_dir), repo_root)
        if provenance is None:
            results.append(
                VendorSyncResult(
                    local_name=target_dir.name,
                    status="skipped",
                    target_dir=rel_target,
                    provenance_path=rel_provenance,
                    message="Skipping prune because provenance is missing.",
                )
            )
            continue
        if _is_git_submodule(repo_root, rel_target):
            results.append(
                VendorSyncResult(
                    local_name=target_dir.name,
                    status="blocked",
                    target_dir=rel_target,
                    provenance_path=rel_provenance,
                    source_url=provenance.source_url,
                    requested_ref=provenance.requested_ref,
                    message="Skipping prune because target is still a legacy submodule.",
                )
            )
            continue
        if dry_run:
            results.append(
                VendorSyncResult(
                    local_name=target_dir.name,
                    status="dry_run",
                    target_dir=rel_target,
                    provenance_path=rel_provenance,
                    source_url=provenance.source_url,
                    requested_ref=provenance.requested_ref,
                    message="Would prune vendor-managed local directory not present in the manifest.",
                )
            )
            continue

        _remove_path(target_dir)
        results.append(
            VendorSyncResult(
                local_name=target_dir.name,
                status="pruned",
                target_dir=rel_target,
                provenance_path=rel_provenance,
                source_url=provenance.source_url,
                requested_ref=provenance.requested_ref,
                message="Pruned vendor-managed local directory not present in the manifest.",
            )
        )

    return results


def sync_skills_sh_official(
    *,
    repo_root: Path,
    manifest_rel: str = DEFAULT_SKILLS_SH_OFFICIAL_MANIFEST,
    prune: bool = False,
    dry_run: bool = False,
) -> list[VendorSyncResult]:
    return sync_vendor_manifest(
        repo_root=repo_root,
        manifest_rel=manifest_rel,
        target_root_rel=DEFAULT_OFFICIAL_TARGET_ROOT,
        import_tool=_OFFICIAL_IMPORT_TOOL,
        prune=prune,
        dry_run=dry_run,
    )


def bootstrap_legacy_imports(
    *,
    repo_root: Path,
    local_name: str | None = None,
    bootstrap_all: bool = False,
    dry_run: bool = False,
) -> list[LegacyBootstrapResult]:
    """Backfill provenance for existing legacy checkouts.

    This is a migration utility for Phase 1 / Phase 2 and is not intended to be
    a permanent day-to-day workflow surface.
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
        rel_target = _repo_rel(target_dir, repo_root)
        rel_provenance = _repo_rel(provenance_path, repo_root)

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
            requested_ref=None,
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


def cleanup_legacy_submodules(
    *,
    repo_root: Path,
    local_name: str | None = None,
    cleanup_all: bool = False,
    apply: bool = False,
) -> list[LegacyCleanupResult]:
    """Convert legacy skill submodules into ignored local vendor artifacts.

    This command is preview-first by default. The expected rollout order is:
    single repo dry-run, single repo --apply, verify, then --all.
    """

    repo_root = repo_root.resolve()
    external_dir = _external_dir(repo_root)
    if local_name:
        candidates = [external_dir / local_name]
    elif cleanup_all:
        candidates = sorted(path for path in external_dir.iterdir() if path.is_dir())
    else:
        raise VendorError("Specify a local name or use --all.")

    gitmodules = _read_gitmodules(repo_root)
    results: list[LegacyCleanupResult] = []

    for target_dir in candidates:
        rel_target = _repo_rel(target_dir, repo_root)
        provenance_path = _provenance_path(target_dir)
        rel_provenance = _repo_rel(provenance_path, repo_root)
        actions = [
            f"verify provenance exists at {rel_provenance}",
            f"verify {rel_target} is still registered as a git submodule",
            f"git submodule deinit -f -- {rel_target}",
            f"git rm --cached -f -- {rel_target}",
            f"remove .git/modules/{rel_target}",
            f"remove {rel_target}/.git",
            f"remove the {rel_target} section from .gitmodules",
            "keep the payload files and .import.json in place as local vendor artifacts",
        ]

        if not target_dir.exists():
            results.append(
                LegacyCleanupResult(
                    local_name=target_dir.name,
                    status="missing",
                    target_dir=rel_target,
                    provenance_path=rel_provenance,
                    actions=actions,
                    message="Target directory does not exist.",
                )
            )
            continue

        if not provenance_path.exists():
            results.append(
                LegacyCleanupResult(
                    local_name=target_dir.name,
                    status="blocked",
                    target_dir=rel_target,
                    provenance_path=rel_provenance,
                    actions=actions,
                    message="Refusing cleanup without provenance. Run bootstrap-legacy first.",
                )
            )
            continue

        is_current_submodule = _is_git_submodule(repo_root, rel_target)
        has_gitmodules_entry = rel_target in gitmodules

        if not has_gitmodules_entry and not is_current_submodule:
            results.append(
                LegacyCleanupResult(
                    local_name=target_dir.name,
                    status="already_clean",
                    target_dir=rel_target,
                    provenance_path=rel_provenance,
                    actions=actions,
                    message="Target is already a vendor-managed local artifact.",
                )
            )
            continue

        if not has_gitmodules_entry:
            results.append(
                LegacyCleanupResult(
                    local_name=target_dir.name,
                    status="blocked",
                    target_dir=rel_target,
                    provenance_path=rel_provenance,
                    actions=actions,
                    message="Refusing cleanup because .gitmodules has no matching legacy entry.",
                )
            )
            continue

        if not is_current_submodule:
            results.append(
                LegacyCleanupResult(
                    local_name=target_dir.name,
                    status="blocked",
                    target_dir=rel_target,
                    provenance_path=rel_provenance,
                    actions=actions,
                    message="Refusing cleanup because the target is not a current git submodule.",
                )
            )
            continue

        if not apply:
            results.append(
                LegacyCleanupResult(
                    local_name=target_dir.name,
                    status="dry_run",
                    target_dir=rel_target,
                    provenance_path=rel_provenance,
                    actions=actions,
                    message="Would convert the legacy git submodule into a vendor-managed local artifact.",
                )
            )
            continue

        backup_root = Path(tempfile.mkdtemp(prefix="ai-config-legacy-cleanup-"))
        backup_dir = backup_root / target_dir.name
        shutil.copytree(target_dir, backup_dir, ignore=shutil.ignore_patterns(".git"))

        try:
            deinit_proc = _run_git(["-C", str(repo_root), "submodule", "deinit", "-f", "--", rel_target], cwd=repo_root, check=False)
            _require_git_success(deinit_proc, f"git submodule deinit for {rel_target}")

            rm_proc = _run_git(["-C", str(repo_root), "rm", "--cached", "-f", "--", rel_target], cwd=repo_root, check=False)
            _require_git_success(rm_proc, f"git rm --cached for {rel_target}")

            _remove_path(repo_root / ".git" / "modules" / Path(rel_target))
            _remove_path(target_dir / ".git")
            _remove_gitmodules_entry(repo_root, rel_target)

            if target_dir.exists():
                _remove_path(target_dir)
            _sync_directory(backup_dir, target_dir)
        finally:
            shutil.rmtree(backup_root, ignore_errors=True)

        results.append(
            LegacyCleanupResult(
                local_name=target_dir.name,
                status="cleaned",
                target_dir=rel_target,
                provenance_path=rel_provenance,
                actions=actions,
                message="Converted legacy git submodule into a vendor-managed local artifact.",
            )
        )

    return results
