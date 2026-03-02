"""CLI entrypoint for selector index build."""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

from ai_config.registry.extractors import collect_all_records
from ai_config.registry.index_builder import (
    DEFAULT_INDEX_DIR,
    EMBEDDING_BACKEND,
    EMBEDDING_MODEL,
    VECTOR_BACKEND,
    build_index,
)
from ai_config.registry.profile_loader import filter_records_by_profile, load_profiles

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


WATCH_DIRS = ("skills", "config", "inventory")


def _snapshot(repo_root: Path) -> dict[str, float]:
    snapshot: dict[str, float] = {}
    for rel_dir in WATCH_DIRS:
        root = repo_root / rel_dir
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file():
                try:
                    snapshot[str(path.relative_to(repo_root).as_posix())] = path.stat().st_mtime
                except OSError:
                    continue
    return snapshot


def _run_build(repo_root: Path, index_dir: Path, embedding_backend: str, vector_backend: str, profile_name: str) -> int:
    records = collect_all_records(repo_root)
    if not records:
        logger.error("No records found. Check skills/, config/, and inventory/.")
        return 1

    profiles = load_profiles(repo_root)
    profile = profiles.get(profile_name)
    if profile is None:
        logger.error("Unknown profile: %s (available=%s)", profile_name, ", ".join(sorted(profiles.keys())))
        return 1

    total = len(records)
    records = filter_records_by_profile(records, profile)
    logger.info(
        "Collected records: total=%d filtered=%d profile=%s",
        total,
        len(records),
        profile.name,
    )
    if not records:
        logger.error("No records left after applying profile=%s", profile.name)
        return 1

    build_index(
        records=records,
        index_dir=index_dir,
        model_name=EMBEDDING_MODEL,
        embedding_backend=embedding_backend,
        vector_backend=vector_backend,
        profile=profile.name,
    )
    logger.info("Index build succeeded at %s", index_dir)
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build selector index from skills/config/inventory.")
    parser.add_argument("--repo-root", type=Path, default=Path("."), help="Repository root path")
    parser.add_argument("--index-dir", type=Path, default=None, help=f"Index output directory (default: {DEFAULT_INDEX_DIR})")
    parser.add_argument("--watch", action="store_true", help="Watch skills/config/inventory and rebuild on changes")
    parser.add_argument("--debounce-sec", type=float, default=1.5, help="Debounce window for watch rebuilds")
    parser.add_argument("--poll-sec", type=float, default=1.0, help="Watch poll interval in seconds")
    parser.add_argument(
        "--embedding-backend",
        choices=("hash", "sentence_transformer"),
        default=EMBEDDING_BACKEND,
        help="Embedding backend",
    )
    parser.add_argument("--vector-backend", choices=("numpy", "faiss"), default=VECTOR_BACKEND, help="Vector backend")
    parser.add_argument("--profile", default="default", help="Index profile name (default: default)")
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    index_dir = (args.index_dir or repo_root / DEFAULT_INDEX_DIR).resolve()
    logger.info("Repo root: %s", repo_root)
    logger.info("Index dir: %s", index_dir)

    exit_code = _run_build(repo_root, index_dir, args.embedding_backend, args.vector_backend, args.profile)
    if exit_code != 0:
        sys.exit(exit_code)

    if not args.watch:
        return

    logger.info("Watch mode started (debounce=%.2fs, poll=%.2fs)", args.debounce_sec, args.poll_sec)
    prev = _snapshot(repo_root)
    changed_at: float | None = None

    while True:
        time.sleep(max(args.poll_sec, 0.2))
        now = _snapshot(repo_root)
        if now != prev:
            changed_at = time.time()
            prev = now
            logger.info("Changes detected in watch targets; waiting for debounce window...")
            continue

        if changed_at is None:
            continue
        if (time.time() - changed_at) < max(args.debounce_sec, 0.0):
            continue

        logger.info("Debounce window elapsed. Rebuilding index...")
        code = _run_build(repo_root, index_dir, args.embedding_backend, args.vector_backend, args.profile)
        if code != 0:
            logger.warning("Rebuild failed during watch loop (continuing).")
        changed_at = None


if __name__ == "__main__":
    main()
