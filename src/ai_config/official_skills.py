"""Official skills.sh coverage status and sync workflow."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml

from ai_config.import_utils import cleanup_clone, clone_source, find_skill_files, normalize_source, sync_directory, utc_now
from ai_config.vendor.skill_vendor import load_vendor_manifest

OFFICIAL_MANIFEST_REL = "config/skills_sh_official.yaml"
OFFICIAL_STATE_REL = "skills/imported/skills-sh/import-state.official.json"
META_FILENAME = ".skills-sh-meta.json"
META_SCHEMA_VERSION = 1
META_ORIGIN = "skills.sh/official"
_GITHUB_SOURCE_PATTERN = re.compile(r"github\.com[:/](?P<creator>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$")


@dataclass(slots=True)
class OfficialSourceEntry:
    creator: str
    repo: str
    github_url: str
    source_key: str

    @property
    def pair(self) -> str:
        return f"{self.creator}/{self.repo}"


@dataclass(slots=True)
class OfficialManifest:
    version: str
    captured_at: str
    source_url: str
    sources: list[OfficialSourceEntry] = field(default_factory=list)

    def pairs(self) -> list[str]:
        return [entry.pair for entry in self.sources]


@dataclass(slots=True)
class OfficialStatusReport:
    version: str
    captured_at: str
    source_url: str
    total_sources: int
    covered_exact: int
    covered_in_imported: int
    covered_in_vendor: int
    missing_exact: int
    missing_pairs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class OfficialSyncResult:
    pair: str
    source_key: str
    status: str
    skill_count: int = 0
    target_dir: str = ""
    source_commit: str = ""
    source_branch: str = ""
    message: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _import_root(repo_root: Path) -> Path:
    return repo_root / "skills" / "imported" / "skills-sh"


def _source_root(repo_root: Path) -> Path:
    return _import_root(repo_root) / "sources"


def _state_path(repo_root: Path) -> Path:
    return repo_root / OFFICIAL_STATE_REL


def _load_yaml(path: Path) -> dict[str, object]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid YAML mapping: {path}")
    return raw


def load_official_manifest(repo_root: Path, manifest_rel: str = OFFICIAL_MANIFEST_REL) -> OfficialManifest:
    manifest_path = repo_root / manifest_rel
    if not manifest_path.exists():
        raise ValueError(f"Official manifest not found: {manifest_rel}")

    raw = _load_yaml(manifest_path)
    sources_raw = raw.get("sources") or []
    if not isinstance(sources_raw, list):
        raise ValueError(f"Official manifest sources must be a list: {manifest_rel}")

    sources: list[OfficialSourceEntry] = []
    seen_keys: set[str] = set()
    seen_pairs: set[str] = set()
    for idx, item in enumerate(sources_raw):
        if not isinstance(item, dict):
            raise ValueError(f"Official manifest entry #{idx + 1} must be a mapping.")
        creator = str(item.get("creator", "")).strip()
        repo = str(item.get("repo", "")).strip()
        github_url = str(item.get("github_url", "")).strip()
        source_key = str(item.get("source_key", "")).strip()
        if not creator or not repo or not github_url or not source_key:
            raise ValueError(f"Official manifest entry #{idx + 1} is missing required fields.")
        pair = f"{creator}/{repo}"
        if source_key != f"{creator}__{repo}":
            raise ValueError(f"Official manifest entry '{pair}' has invalid source_key '{source_key}'.")
        if pair in seen_pairs:
            raise ValueError(f"Duplicate official pair in manifest: {pair}")
        if source_key in seen_keys:
            raise ValueError(f"Duplicate official source_key in manifest: {source_key}")
        seen_pairs.add(pair)
        seen_keys.add(source_key)
        sources.append(
            OfficialSourceEntry(
                creator=creator,
                repo=repo,
                github_url=github_url,
                source_key=source_key,
            )
        )

    return OfficialManifest(
        version=str(raw.get("version", "1.0.0")),
        captured_at=str(raw.get("captured_at", "")),
        source_url=str(raw.get("source_url", "")),
        sources=sources,
    )


def _parse_github_pair(source_url: str) -> str | None:
    normalized = source_url.strip()
    match = _GITHUB_SOURCE_PATTERN.search(normalized)
    if not match:
        return None
    return f"{match.group('creator')}/{match.group('repo')}"


def _source_dir_has_skill(path: Path) -> bool:
    if not path.is_dir():
        return False
    return any(path.rglob("SKILL.md"))


def _imported_exact_pairs(repo_root: Path) -> set[str]:
    source_root = _source_root(repo_root)
    if not source_root.is_dir():
        return set()

    pairs: set[str] = set()
    for source_dir in sorted(path for path in source_root.iterdir() if path.is_dir() and "__" in path.name):
        if not _source_dir_has_skill(source_dir):
            continue
        creator, repo = source_dir.name.split("__", 1)
        pairs.add(f"{creator}/{repo}")
    return pairs


def _vendor_exact_pairs(repo_root: Path) -> set[str]:
    pairs: set[str] = set()
    try:
        manifest = load_vendor_manifest(repo_root)
    except Exception:
        return pairs

    for entry in manifest.sources:
        pair = _parse_github_pair(entry.source_url)
        if pair:
            pairs.add(pair)
    return pairs


def build_official_status(repo_root: Path, manifest_rel: str = OFFICIAL_MANIFEST_REL) -> OfficialStatusReport:
    repo_root = repo_root.resolve()
    manifest = load_official_manifest(repo_root, manifest_rel)
    official_pairs = set(manifest.pairs())
    imported_pairs = _imported_exact_pairs(repo_root) & official_pairs
    vendor_pairs = _vendor_exact_pairs(repo_root) & official_pairs
    covered_pairs = imported_pairs | vendor_pairs
    missing_pairs = [entry.pair for entry in manifest.sources if entry.pair not in covered_pairs]

    return OfficialStatusReport(
        version=manifest.version,
        captured_at=manifest.captured_at,
        source_url=manifest.source_url,
        total_sources=len(manifest.sources),
        covered_exact=len(covered_pairs),
        covered_in_imported=len(imported_pairs),
        covered_in_vendor=len(vendor_pairs),
        missing_exact=len(missing_pairs),
        missing_pairs=missing_pairs,
    )


def _write_meta(
    *,
    dest_dir: Path,
    entry: OfficialSourceEntry,
    skill_id: str,
    source_path: str,
    imported_at: str,
    source_commit: str,
    source_branch: str,
    manifest: OfficialManifest,
) -> None:
    payload = {
        "schemaVersion": META_SCHEMA_VERSION,
        "origin": META_ORIGIN,
        "capturedAt": manifest.captured_at,
        "importedAt": imported_at,
        "updatedAt": imported_at,
        "source": entry.pair,
        "sourceKey": entry.source_key,
        "skillId": skill_id,
        "name": skill_id,
        "sourceCommit": source_commit,
        "sourceBranch": source_branch,
        "sourcePath": source_path,
    }
    (dest_dir / META_FILENAME).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def sync_official_skills(
    repo_root: Path,
    *,
    manifest_rel: str = OFFICIAL_MANIFEST_REL,
    dry_run: bool = False,
) -> tuple[OfficialStatusReport, list[OfficialSyncResult]]:
    repo_root = repo_root.resolve()
    manifest = load_official_manifest(repo_root, manifest_rel)
    status = build_official_status(repo_root, manifest_rel)
    missing_pairs = set(status.missing_pairs)
    missing = {entry.pair: entry for entry in manifest.sources if entry.pair in missing_pairs}

    results: list[OfficialSyncResult] = []
    source_root = _source_root(repo_root)

    if dry_run:
        for pair in status.missing_pairs:
            entry = missing[pair]
            results.append(
                OfficialSyncResult(
                    pair=pair,
                    source_key=entry.source_key,
                    status="dry_run",
                    target_dir=str((_source_root(repo_root) / entry.source_key).relative_to(repo_root)),
                    message="Would import missing official source.",
                )
            )
        return status, results

    source_root.mkdir(parents=True, exist_ok=True)

    for pair in status.missing_pairs:
        entry = missing[pair]
        target_dir = source_root / entry.source_key
        normalized_source = normalize_source(entry.github_url)
        clone_dir: Path | None = None
        commit_sha = ""
        clone_branch = ""
        try:
            clone_dir, commit_sha, clone_branch = clone_source(
                normalized_source,
                branch=None,
                ref=None,
                shallow=True,
                archive_fallback=True,
                clone_timeout=30,
            )
            skill_files = find_skill_files(clone_dir)
            if not skill_files:
                results.append(
                    OfficialSyncResult(
                        pair=pair,
                        source_key=entry.source_key,
                        status="failed",
                        target_dir=str(target_dir.relative_to(repo_root)),
                        source_commit=commit_sha,
                        source_branch=clone_branch,
                        error="No SKILL.md files found in source repo.",
                        message="Official source did not contain any SKILL.md files.",
                    )
                )
                continue

            imported_at = utc_now()
            target_dir.mkdir(parents=True, exist_ok=True)

            for skill_file in skill_files:
                skill_dir = skill_file.parent
                source_path = (
                    str(skill_dir.relative_to(clone_dir).as_posix()) if skill_dir != clone_dir else "."
                )
                skill_id = skill_dir.name if skill_dir != clone_dir else entry.repo
                dest_dir = target_dir / skill_id
                sync_directory(skill_dir, dest_dir)
                _write_meta(
                    dest_dir=dest_dir,
                    entry=entry,
                    skill_id=skill_id,
                    source_path=source_path,
                    imported_at=imported_at,
                    source_commit=commit_sha,
                    source_branch=clone_branch,
                    manifest=manifest,
                )

            results.append(
                OfficialSyncResult(
                    pair=pair,
                    source_key=entry.source_key,
                    status="imported",
                    skill_count=len(skill_files),
                    target_dir=str(target_dir.relative_to(repo_root)),
                    source_commit=commit_sha,
                    source_branch=clone_branch,
                    message=f"Imported {len(skill_files)} skill(s).",
                )
            )
        except Exception as exc:
            error_text = exc.stderr.strip() if hasattr(exc, "stderr") and exc.stderr else str(exc)
            results.append(
                OfficialSyncResult(
                    pair=pair,
                    source_key=entry.source_key,
                    status="failed",
                    target_dir=str(target_dir.relative_to(repo_root)),
                    source_commit=commit_sha,
                    source_branch=clone_branch,
                    error=error_text,
                    message="Import failed.",
                )
            )
        finally:
            if clone_dir is not None:
                cleanup_clone(clone_dir)

    final_status = build_official_status(repo_root, manifest_rel)
    state = {
        "schemaVersion": 1,
        "generatedAt": utc_now(),
        "manifestPath": str((repo_root / manifest_rel).relative_to(repo_root)),
        "status": final_status.to_dict(),
        "results": [result.to_dict() for result in results],
    }
    _state_path(repo_root).write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return final_status, results


def _print_status(report: OfficialStatusReport) -> None:
    print(f"Official manifest captured_at: {report.captured_at}")
    print(f"Source URL: {report.source_url}")
    print(
        "Coverage: "
        f"total={report.total_sources} "
        f"covered_exact={report.covered_exact} "
        f"covered_in_imported={report.covered_in_imported} "
        f"covered_in_vendor={report.covered_in_vendor} "
        f"missing_exact={report.missing_exact}"
    )
    if report.missing_pairs:
        print("Missing pairs:")
        for pair in report.missing_pairs:
            print(f"  - {pair}")


def _print_sync(results: list[OfficialSyncResult]) -> None:
    for result in results:
        print(f"{result.pair}: {result.status}")
        if result.target_dir:
            print(f"  target: {result.target_dir}")
        if result.skill_count:
            print(f"  skills: {result.skill_count}")
        if result.source_commit:
            print(f"  commit: {result.source_commit[:12]}")
        if result.message:
            print(f"  message: {result.message}")
        if result.error:
            print(f"  error: {result.error}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="skills.sh official coverage status and sync")
    subparsers = parser.add_subparsers(dest="command", required=True)

    status_p = subparsers.add_parser("status", help="Inspect official coverage")
    status_p.add_argument("--repo-root", default=".", help="Repo root (default: current directory)")
    status_p.add_argument("--json", action="store_true", help="Emit JSON")

    sync_p = subparsers.add_parser("sync", help="Import missing exact official sources")
    sync_p.add_argument("--repo-root", default=".", help="Repo root (default: current directory)")
    sync_p.add_argument("--dry-run", action="store_true", help="Report what would be imported without mutating")
    sync_p.add_argument("--json", action="store_true", help="Emit JSON")

    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root).resolve()

    if args.command == "status":
        report = build_official_status(repo_root)
        if args.json:
            print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        else:
            _print_status(report)
        return 0

    report, results = sync_official_skills(repo_root, dry_run=bool(args.dry_run))
    failed = [result for result in results if result.status == "failed"]
    payload = {
        "status": report.to_dict(),
        "results": [result.to_dict() for result in results],
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        _print_status(report)
        _print_sync(results)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
