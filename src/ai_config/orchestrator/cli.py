"""CLI entrypoint for the agent orchestrator.

Usage:
    python -m ai_config.orchestrator.cli "フロントエンド開発のためのツールを探して"
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="AI Config Agent - Dynamic tool orchestrator")
    parser.add_argument("query", type=str, help="User request / question")
    parser.add_argument(
        "--index-dir",
        type=Path,
        default=Path(".index"),
        help="Path to the pre-built index directory (default: .index)",
    )
    parser.add_argument(
        "--search-only",
        action="store_true",
        help="Only search tools, skip LLM planning and execution",
    )
    args = parser.parse_args(argv)

    index_dir = args.index_dir.resolve()
    if not (index_dir / "records.json").exists():
        logger.error("Index not found at %s. Run 'python -m ai_config.build_index' first.", index_dir)
        sys.exit(1)

    if args.search_only:
        # Quick search mode: no LLM needed
        from ai_config.retriever.hybrid_search import HybridRetriever

        retriever = HybridRetriever(index_dir)
        print(retriever.search_text(args.query))
        return

    # Full orchestrator mode
    from ai_config.orchestrator.graph import create_agent
    from ai_config.orchestrator import nodes

    # Point retriever to the correct index
    nodes._retriever = None  # Reset so it picks up the new index dir

    # Monkey-patch index dir (simple approach for CLI)
    original_get = nodes._get_retriever

    def patched_get(d=None):
        return original_get(index_dir)

    nodes._get_retriever = patched_get

    agent = create_agent()

    initial_state = {
        "query": args.query,
        "retrieved_tools": [],
        "plan": "",
        "execution_results": [],
        "error": None,
        "retry_count": 0,
        "final_answer": "",
    }

    logger.info("Running agent with query: %s", args.query)
    result = agent.invoke(initial_state)

    print("\n" + "=" * 60)
    print(result.get("final_answer", "(no answer)"))
    print("=" * 60)


if __name__ == "__main__":
    main()
