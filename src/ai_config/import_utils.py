"""Shared git/materialization helpers for repo-import workflows."""

from __future__ import annotations

import re
import shutil
import subprocess
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

_GITHUB_REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_GIT_URL_PREFIXES = ("https://", "http://", "git@", "ssh://", "file://")
_GITHUB_HOSTS = {"github.com", "www.github.com"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_git(
    args: list[str],
    *,
    cwd: Path,
    check: bool = True,
    timeout: float | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=check, timeout=timeout)


def normalize_source(source: str) -> str:
    raw = source.strip()
    if not raw:
        raise ValueError("Source must not be empty.")
    if raw.startswith(_GIT_URL_PREFIXES):
        return raw

    possible_path = Path(raw).expanduser()
    if possible_path.exists():
        return str(possible_path.resolve())

    if _GITHUB_REPO_PATTERN.fullmatch(raw):
        return f"https://github.com/{raw}.git"

    raise ValueError(f"Cannot parse source: {source}")


def derive_local_name(source: str) -> str:
    trimmed = source.rstrip("/").split("/")[-1]
    if trimmed.endswith(".git"):
        trimmed = trimmed[:-4]
    if trimmed:
        return trimmed
    raise ValueError(f"Cannot derive local name from source: {source}")


def find_skill_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("SKILL.md") if ".git" not in path.parts)


def remove_path(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
        return
    path.unlink()


def sync_directory(src_dir: Path, dest_dir: Path, *, preserve_names: set[str] | None = None) -> None:
    preserve_names = preserve_names or set()
    dest_dir.mkdir(parents=True, exist_ok=True)

    source_names: set[str] = set()
    for child in src_dir.iterdir():
        if child.name == ".git":
            continue
        source_names.add(child.name)
        target = dest_dir / child.name
        remove_path(target)
        if child.is_dir():
            shutil.copytree(child, target, ignore=shutil.ignore_patterns(".git"))
        else:
            shutil.copy2(child, target)

    for child in list(dest_dir.iterdir()):
        if child.name in preserve_names or child.name in source_names:
            continue
        remove_path(child)


def _parse_github_repo(source: str) -> tuple[str, str] | None:
    parsed = urlparse(source)
    if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() not in _GITHUB_HOSTS:
        return None

    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        return None
    repo = parts[1]
    if repo.endswith(".git"):
        repo = repo[:-4]
    return parts[0], repo


def _resolve_github_head(source: str, *, cwd: Path) -> tuple[str, str]:
    result = run_git(["ls-remote", "--symref", source, "HEAD"], cwd=cwd)
    branch = ""
    commit_sha = ""
    for line in result.stdout.splitlines():
        if line.startswith("ref: "):
            ref_name = line.split("\t", 1)[0][5:]
            if ref_name.startswith("refs/heads/"):
                branch = ref_name.removeprefix("refs/heads/")
        elif line.endswith("\tHEAD"):
            commit_sha = line.split("\t", 1)[0]

    if not branch or not commit_sha:
        raise ValueError(f"Failed to resolve GitHub HEAD for {source}")
    return branch, commit_sha


def _safe_extract_tar(archive_path: Path, dest_dir: Path) -> Path:
    dest_root = dest_dir.resolve()
    with tarfile.open(archive_path, "r:gz") as archive:
        members = archive.getmembers()
        for member in members:
            target = (dest_root / member.name).resolve()
            if target != dest_root and dest_root not in target.parents:
                raise ValueError(f"Unsafe archive path detected: {member.name}")
        archive.extractall(dest_root)

    extracted_dirs = [child for child in dest_dir.iterdir() if child.is_dir()]
    if len(extracted_dirs) != 1:
        raise ValueError(f"Expected exactly one extracted directory in {dest_dir}")
    return extracted_dirs[0]


def _download_github_archive(source: str, *, temp_dir: Path, clone_dir: Path) -> tuple[str, str]:
    parsed = _parse_github_repo(source)
    if parsed is None:
        raise ValueError(f"GitHub archive fallback does not support source: {source}")

    owner, repo = parsed
    branch, commit_sha = _resolve_github_head(source, cwd=temp_dir)
    archive_path = temp_dir / "repo.tar.gz"
    archive_url = f"https://codeload.github.com/{owner}/{repo}/tar.gz/{commit_sha}"
    with urlopen(archive_url, timeout=120) as response, archive_path.open("wb") as handle:
        shutil.copyfileobj(response, handle)

    extracted_dir = _safe_extract_tar(archive_path, temp_dir)
    archive_path.unlink(missing_ok=True)
    extracted_dir.rename(clone_dir)
    return commit_sha, branch


def clone_source(
    source: str,
    *,
    branch: str | None,
    ref: str | None,
    shallow: bool = False,
    archive_fallback: bool = False,
    clone_timeout: float | None = None,
) -> tuple[Path, str, str]:
    temp_dir = Path(tempfile.mkdtemp(prefix="ai-config-import-"))
    clone_dir = temp_dir / "repo"
    clone_args = ["clone", "--quiet"]
    if shallow and not ref:
        clone_args.extend(["--depth", "1", "--filter=blob:none", "--single-branch", "--no-tags"])
    if branch and not ref:
        clone_args.extend(["--branch", branch])
    clone_args.extend([source, str(clone_dir)])
    try:
        run_git(clone_args, cwd=temp_dir, timeout=clone_timeout)
        if ref:
            run_git(["checkout", "--quiet", ref], cwd=clone_dir)
        elif branch:
            run_git(["checkout", "--quiet", branch], cwd=clone_dir, check=False)
        commit_sha = run_git(["rev-parse", "HEAD"], cwd=clone_dir).stdout.strip()
        clone_branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=clone_dir).stdout.strip()
        if clone_branch == "HEAD":
            clone_branch = branch or ""
        return clone_dir, commit_sha, clone_branch
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        if archive_fallback and shallow and not ref and _parse_github_repo(source) is not None:
            remove_path(clone_dir)
            commit_sha, clone_branch = _download_github_archive(source, temp_dir=temp_dir, clone_dir=clone_dir)
            return clone_dir, commit_sha, clone_branch
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def cleanup_clone(clone_dir: Path) -> None:
    shutil.rmtree(clone_dir.parent, ignore_errors=True)
