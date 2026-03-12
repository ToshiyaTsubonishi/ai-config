"""CLI for the repo-managed vendor layer.

Phase 1 intentionally keeps skill plumbing inside this repository instead of
directly adopting vercel-labs/skills. The missing --path support upstream is
handled here by a repo-local vendor CLI that preserves skills/external as the
stable scan target for selector/index/retrieval.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from ai_config.vendor.models import LegacyBootstrapResult, VendorImportResult, VendorImportSpec
from ai_config.vendor.skill_vendor import (
    VendorError,
    bootstrap_legacy_imports,
    import_skill_repo,
    remove_imported_skill,
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Manage repo-local external skill imports for ai-config. "
            "Phase 1 keeps skills/external as the stable scan target instead of "
            "directly adopting vercel-labs/skills."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."), help="Repository root path")

    sub = parser.add_subparsers(dest="command", required=True)

    import_p = sub.add_parser("import", help="Import an external skill repo into skills/external/")
    import_p.add_argument("source", help="GitHub repo, git URL, file URL, or local git checkout")
    import_p.add_argument("local_name", nargs="?", help="Local target directory name")
    import_p.add_argument("--branch", help="Branch to clone")
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
    except VendorError as error:
        logger.error("%s", error)
        return 1

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
