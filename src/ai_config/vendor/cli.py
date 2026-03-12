"""CLI for the repo-managed vendor layer.

Phase 2 keeps skill plumbing inside this repository instead of directly
adopting vercel-labs/skills. The missing --path support upstream is handled
here by a repo-local vendor CLI that preserves skills/external as the stable
scan target for selector/index/retrieval while moving legacy submodules to
vendor-managed local artifacts.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from ai_config.vendor.models import (
    DEFAULT_VENDOR_MANIFEST,
    LegacyBootstrapResult,
    LegacyCleanupResult,
    VendorImportResult,
    VendorImportSpec,
    VendorStatusReport,
    VendorSyncResult,
)
from ai_config.vendor.skill_vendor import (
    VendorError,
    bootstrap_legacy_imports,
    cleanup_legacy_submodules,
    import_skill_repo,
    inspect_vendor_state,
    load_vendor_manifest,
    remove_imported_skill,
    sync_vendor_manifest,
    update_imported_skills,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def _print_import_result(result: VendorImportResult) -> None:
    print(f"{result.local_name}: {result.status}")
    if result.message:
        print(f"  {result.message}")
    if result.target_dir:
        print(f"  target: {result.target_dir}")
    if result.provenance_path:
        print(f"  provenance: {result.provenance_path}")
    if result.skill_count:
        print(f"  skills: {result.skill_count}")
    if result.orphaned_dirs:
        print(f"  orphaned: {', '.join(result.orphaned_dirs)}")


def _print_bootstrap_result(result: LegacyBootstrapResult) -> None:
    print(f"{result.local_name}: {result.status}")
    if result.message:
        print(f"  {result.message}")
    if result.source_url:
        print(f"  source: {result.source_url}")
    if result.target_dir:
        print(f"  target: {result.target_dir}")
    if result.provenance_path:
        print(f"  provenance: {result.provenance_path}")
    if result.skill_count:
        print(f"  skills: {result.skill_count}")


def _print_sync_result(result: VendorSyncResult) -> None:
    print(f"{result.local_name}: {result.status}")
    if result.message:
        print(f"  {result.message}")
    if result.source_url:
        print(f"  source: {result.source_url}")
    if result.target_dir:
        print(f"  target: {result.target_dir}")
    if result.provenance_path:
        print(f"  provenance: {result.provenance_path}")
    if result.requested_ref:
        print(f"  ref: {result.requested_ref}")


def _print_cleanup_result(result: LegacyCleanupResult) -> None:
    print(f"{result.local_name}: {result.status}")
    if result.message:
        print(f"  {result.message}")
    if result.target_dir:
        print(f"  target: {result.target_dir}")
    if result.provenance_path:
        print(f"  provenance: {result.provenance_path}")
    for action in result.actions:
        print(f"  - {action}")


def _print_status_report(report: VendorStatusReport) -> None:
    summary = report.summary
    print(f"Vendor status at {report.generated_at}")
    print(f"  repo: {report.repo_root}")
    print(f"  manifest: {report.manifest_path}")
    print(
        "  summary: "
        f"ready={summary.ready} "
        f"needs_align={summary.needs_align} "
        f"needs_sync={summary.needs_sync} "
        f"missing={summary.missing} "
        f"legacy_submodule={summary.legacy_submodule} "
        f"missing_provenance={summary.missing_provenance} "
        f"extra_local={summary.extra_local} "
        f"unmanaged_local={summary.unmanaged_local}"
    )
    if report.manifest_errors:
        print("  manifest_errors:")
        for error in report.manifest_errors:
            print(f"    - {error}")

    print(f"{'Local Name':<36} {'Status':<18} {'Ref':<12} {'Commit':<12} {'Skills':<6} {'Ignored':<7}")
    print("-" * 100)
    for entry in report.entries:
        manifest_ref = (entry.manifest_ref or "-")[:12]
        commit_sha = (entry.provenance_commit_sha or "-")[:12]
        ignored = "yes" if entry.git_ignored else "no"
        print(
            f"{entry.local_name:<36} {entry.status:<18} {manifest_ref:<12} "
            f"{commit_sha:<12} {entry.skill_count:<6} {ignored:<7}"
        )
        if entry.message and entry.status != "ready":
            print(f"  {entry.message}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Manage repo-local external skill imports for ai-config. "
            "Phase 2 keeps skills/external as the stable scan target instead of "
            "directly adopting vercel-labs/skills."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."), help="Repository root path")

    sub = parser.add_subparsers(dest="command", required=True)

    import_p = sub.add_parser("import", help="Import an external skill repo into skills/external/")
    import_p.add_argument("source", help="GitHub repo, git URL, file URL, or local git checkout")
    import_p.add_argument("local_name", nargs="?", help="Local target directory name")
    import_p.add_argument("--branch", help="Branch to clone")
    import_p.add_argument("--ref", help="Exact git ref or commit to materialize")
    import_p.add_argument("--force", action="store_true", help="Force re-import even if SHA is unchanged")
    import_p.add_argument("--dry-run", action="store_true", help="Show what would happen without writing files")

    update_p = sub.add_parser("update", help="Update imported skills using .import.json provenance")
    update_p.add_argument("local_name", nargs="?", help="Specific imported repo to update")
    update_p.add_argument("--all", action="store_true", help="Update every imported repo with provenance metadata")
    update_p.add_argument("--force", action="store_true", help="Force re-import even if SHA is unchanged")
    update_p.add_argument("--dry-run", action="store_true", help="Show what would happen without writing files")

    remove_p = sub.add_parser(
        "remove",
        help="Remove a vendor-managed skills/external checkout. Config cleanup stays with ai-config-sources.",
    )
    remove_p.add_argument("local_name", help="Imported repo directory to remove from skills/external")
    remove_p.add_argument("--dry-run", action="store_true", help="Show what would happen without writing files")

    bootstrap_p = sub.add_parser(
        "bootstrap-legacy",
        help=(
            "Temporary migration utility: backfill .import.json for existing legacy checkouts. "
            "Not intended as a permanent day-to-day command."
        ),
    )
    bootstrap_p.add_argument("local_name", nargs="?", help="Specific legacy checkout to backfill")
    bootstrap_p.add_argument("--all", action="store_true", help="Backfill provenance for every skills/external/* repo")
    bootstrap_p.add_argument("--dry-run", action="store_true", help="Show what would happen without writing files")

    sync_p = sub.add_parser(
        "sync-manifest",
        help=(
            "Materialize config/vendor_skills.yaml into skills/external/. "
            "Pinned refs are required; pruning is opt-in."
        ),
    )
    sync_p.add_argument(
        "--manifest",
        default=DEFAULT_VENDOR_MANIFEST,
        help=f"Vendor manifest file relative path (default: {DEFAULT_VENDOR_MANIFEST})",
    )
    sync_p.add_argument("--prune", action="store_true", help="Prune vendor-managed dirs not present in the manifest")
    sync_p.add_argument("--dry-run", action="store_true", help="Show what would happen without writing files")

    cleanup_p = sub.add_parser(
        "cleanup-legacy-submodule",
        help=(
            "Temporary migration utility: preview-first conversion of legacy skill submodules into "
            "local vendor artifacts. Run single-repo dry-run, single-repo --apply, verify, then --all."
        ),
    )
    cleanup_p.add_argument("local_name", nargs="?", help="Specific legacy checkout to convert")
    cleanup_p.add_argument("--all", action="store_true", help="Convert every legacy skill submodule under skills/external/")
    cleanup_p.add_argument(
        "--apply",
        action="store_true",
        help="Apply the cleanup steps. Default is preview-only dry-run semantics.",
    )

    status_p = sub.add_parser(
        "status",
        help="Inspect vendor-managed external skills and local payload state without mutating anything.",
    )
    status_p.add_argument(
        "--manifest",
        default=DEFAULT_VENDOR_MANIFEST,
        help=f"Vendor manifest file relative path (default: {DEFAULT_VENDOR_MANIFEST})",
    )
    status_p.add_argument("--json", action="store_true", help="Print structured JSON output")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()

    try:
        if args.command == "import":
            result = import_skill_repo(
                VendorImportSpec(
                    source_url=args.source,
                    local_name=args.local_name,
                    branch=args.branch,
                    ref=args.ref,
                    force=args.force,
                    dry_run=args.dry_run,
                ),
                repo_root=repo_root,
            )
            _print_import_result(result)
            if result.status in {"imported", "updated", "removed"}:
                print("Hint: Run 'ai-config-index --repo-root . --profile default' to rebuild the selector index.")
            return 0

        if args.command == "update":
            results = update_imported_skills(
                repo_root=repo_root,
                local_name=args.local_name,
                update_all=args.all,
                force=args.force,
                dry_run=args.dry_run,
            )
            for result in results:
                _print_import_result(result)
            if any(result.status in {"imported", "updated"} for result in results):
                print("Hint: Run 'ai-config-index --repo-root . --profile default' to rebuild the selector index.")
            return 0

        if args.command == "remove":
            result = remove_imported_skill(repo_root=repo_root, local_name=args.local_name, dry_run=args.dry_run)
            _print_import_result(result)
            if result.status == "removed":
                print("Hint: Run 'ai-config-index --repo-root . --profile default' to rebuild the selector index.")
            return 0

        if args.command == "bootstrap-legacy":
            results = bootstrap_legacy_imports(
                repo_root=repo_root,
                local_name=args.local_name,
                bootstrap_all=args.all,
                dry_run=args.dry_run,
            )
            for result in results:
                _print_bootstrap_result(result)
            return 0

        if args.command == "sync-manifest":
            load_vendor_manifest(repo_root, args.manifest)
            results = sync_vendor_manifest(
                repo_root=repo_root,
                manifest_rel=args.manifest,
                prune=args.prune,
                dry_run=args.dry_run,
            )
            for result in results:
                _print_sync_result(result)
            if any(result.status in {"imported", "updated", "pruned", "aligned"} for result in results):
                print("Hint: Run 'ai-config-index --repo-root . --profile default' to rebuild the selector index.")
            if any(result.status == "blocked" for result in results):
                return 1
            return 0

        if args.command == "cleanup-legacy-submodule":
            results = cleanup_legacy_submodules(
                repo_root=repo_root,
                local_name=args.local_name,
                cleanup_all=args.all,
                apply=args.apply,
            )
            for result in results:
                _print_cleanup_result(result)
            if any(result.status == "blocked" for result in results):
                return 1
            return 0

        if args.command == "status":
            report = inspect_vendor_state(repo_root=repo_root, manifest_rel=args.manifest)
            if args.json:
                print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
            else:
                _print_status_report(report)
            return 0
    except VendorError as error:
        logger.error("%s", error)
        return 1

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
