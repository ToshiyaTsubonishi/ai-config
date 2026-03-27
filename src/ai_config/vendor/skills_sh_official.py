"""skills.sh official source discovery and manifest refresh helpers."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Callable
from urllib.request import Request, urlopen

import yaml

from ai_config.vendor.models import (
    DEFAULT_SKILLS_SH_OFFICIAL_MANIFEST,
    DEFAULT_SKILLS_SH_OFFICIAL_SKIPPED_REPORT,
)
from ai_config.vendor.skill_vendor import VendorError, _utc_now

SKILLS_SH_OFFICIAL_URL = "https://skills.sh/official"

_SKILLS_SH_REPO_PATTERN = re.compile(r'\\"repo\\":\\"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)\\"')
_DEFAULT_BRANCH_PATTERN = re.compile(r"^ref:\s+refs/heads/([^\t]+)\tHEAD$", re.MULTILINE)
_HEAD_SHA_PATTERN = re.compile(r"^([0-9a-f]{40})\tHEAD$", re.MULTILINE)


def fetch_skills_sh_official_html(source_url: str = SKILLS_SH_OFFICIAL_URL) -> str:
    request = Request(source_url, headers={"User-Agent": "ai-config/0.1 skills.sh-official-refresh"})
    with urlopen(request) as response:  # noqa: S310 - fixed official catalog URL
        return response.read().decode("utf-8", errors="ignore")


def extract_skills_sh_official_repo_slugs(html: str) -> list[str]:
    repo_slugs = sorted(set(_SKILLS_SH_REPO_PATTERN.findall(html)))
    if not repo_slugs:
        raise VendorError("No official repo slugs found in skills.sh official page payload.")
    return repo_slugs


def sanitize_skills_sh_repo_slug(repo_slug: str) -> str:
    return repo_slug.replace("/", "__")


def resolve_skills_sh_repo_head(repo_slug: str) -> tuple[str, str]:
    source_url = f"https://github.com/{repo_slug}.git"
    proc = subprocess.run(
        ["git", "ls-remote", "--symref", source_url, "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "unknown git error").strip()
        raise VendorError(f"Cannot resolve {repo_slug}: {detail}")

    default_branch_match = _DEFAULT_BRANCH_PATTERN.search(proc.stdout or "")
    head_sha_match = _HEAD_SHA_PATTERN.search(proc.stdout or "")
    if not default_branch_match or not head_sha_match:
        raise VendorError(f"Cannot parse default branch and HEAD SHA for {repo_slug}.")

    return default_branch_match.group(1), head_sha_match.group(1)


def refresh_skills_sh_official_manifest(
    *,
    repo_root: Path,
    manifest_rel: str = DEFAULT_SKILLS_SH_OFFICIAL_MANIFEST,
    skipped_report_rel: str = DEFAULT_SKILLS_SH_OFFICIAL_SKIPPED_REPORT,
    source_url: str = SKILLS_SH_OFFICIAL_URL,
    html: str | None = None,
    resolver: Callable[[str], tuple[str, str]] | None = None,
) -> dict[str, object]:
    repo_root = repo_root.resolve()
    html = html if html is not None else fetch_skills_sh_official_html(source_url)
    repo_slugs = extract_skills_sh_official_repo_slugs(html)
    resolver = resolver or resolve_skills_sh_repo_head

    generated_at = _utc_now()
    sources: dict[str, dict[str, str]] = {}
    skipped: list[dict[str, str]] = []

    for repo_slug in repo_slugs:
        try:
            branch, ref = resolver(repo_slug)
        except VendorError as error:
            skipped.append({"repo_slug": repo_slug, "error": str(error)})
            continue

        local_name = sanitize_skills_sh_repo_slug(repo_slug)
        sources[local_name] = {
            "repo_slug": repo_slug,
            "source_url": f"https://github.com/{repo_slug}.git",
            "local_name": local_name,
            "branch": branch,
            "ref": ref,
        }

    manifest_payload = {
        "version": "1.0.0",
        "generated_at": generated_at,
        "source_url": source_url,
        "total_discovered": len(repo_slugs),
        "total_public": len(sources),
        "sources": sources,
    }
    manifest_path = repo_root / manifest_rel
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        yaml.safe_dump(manifest_payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    skipped_payload = {
        "generated_at": generated_at,
        "source_url": source_url,
        "total_discovered": len(repo_slugs),
        "total_public": len(sources),
        "total_skipped": len(skipped),
        "skipped": skipped,
    }
    skipped_path = repo_root / skipped_report_rel
    skipped_path.parent.mkdir(parents=True, exist_ok=True)
    skipped_path.write_text(json.dumps(skipped_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "manifest_path": manifest_path.relative_to(repo_root).as_posix(),
        "skipped_report_path": skipped_path.relative_to(repo_root).as_posix(),
        "total_discovered": len(repo_slugs),
        "total_public": len(sources),
        "total_skipped": len(skipped),
    }
