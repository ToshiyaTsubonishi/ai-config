"""CLI entrypoint: build the tool registry index.

Usage:
    python -m ai_config.build_index --repo-root /path/to/ai-config-sync
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from ai_config.registry.skill_parser import scan_skills
from ai_config.registry.mcp_parser import scan_mcp_servers
from ai_config.registry.index_builder import build_index, DEFAULT_INDEX_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Build FAISS + BM25 indexes from skills/ and MCP configs"
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Root of the ai-config-sync repository (default: cwd)",
    )
    parser.add_argument(
        "--index-dir",
        type=Path,
        default=None,
        help=f"Output directory for indexes (default: <repo-root>/{DEFAULT_INDEX_DIR})",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    index_dir = (args.index_dir or repo_root / DEFAULT_INDEX_DIR).resolve()

    logger.info("Repo root: %s", repo_root)
    logger.info("Index dir: %s", index_dir)

    # ---------- Collect all tool records ----------
    skills = scan_skills(repo_root)
    mcp_servers = scan_mcp_servers(repo_root)
    all_records = skills + mcp_servers

    if not all_records:
        logger.error("No tools found. Check that skills/ and config/ exist.")
        sys.exit(1)

    logger.info("Total records: %d (skills=%d, mcp=%d)", len(all_records), len(skills), len(mcp_servers))

    # ---------- Build indexes ----------
    build_index(all_records, index_dir)
    logger.info("✅ Index build completed successfully.")


if __name__ == "__main__":
    main()
