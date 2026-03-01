"""CLI entrypoint for LangGraph orchestrator."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

from ai_config.orchestrator.graph import create_agent
from ai_config.retriever.hybrid_search import HybridRetriever
from ai_config.retriever.query_intent import infer_query_intent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def _print_search_only(index_dir: Path, query: str, top_k: int) -> None:
    retriever = HybridRetriever(index_dir)
    intent = infer_query_intent(query)
    hits = retriever.search(
        query=query,
        top_k=top_k,
        tool_kinds=intent.tool_kinds or None,
        targets=intent.targets or None,
        capabilities=intent.capabilities or None,
    )
    if not hits:
        print("No tools found.")
        return
    for idx, hit in enumerate(hits, start=1):
        payload = hit.to_dict()
        score = payload["score_breakdown"]
        print(
            f"{idx}. [{payload['tool_kind']}] {payload['name']} "
            f"(rrf={score['rrf']:.4f}, sem={score['semantic']:.4f}, bm25={score['bm25']:.4f})"
        )
        print(f"   id={payload['id']} source={payload['source_path']}")
        print(f"   {payload['description'][:140]}")


def main(argv: list[str] | None = None) -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="ai-config dynamic tool orchestrator")
    parser.add_argument("query", type=str, help="User query")
    parser.add_argument("--index-dir", type=Path, default=Path(".index"), help="Index directory")
    parser.add_argument("--search-only", action="store_true", help="Run retriever only")
    parser.add_argument("--max-retries", type=int, default=2, help="Maximum re-retrieve retries")
    parser.add_argument("--top-k", type=int, default=8, help="Retriever top-k")
    parser.add_argument("--trace", action="store_true", help="Print execution trace JSON")
    args = parser.parse_args(argv)

    index_dir = args.index_dir.resolve()
    if not (index_dir / "summary.json").exists():
        logger.error("Index artifacts not found: %s. Run ai-config-index first.", index_dir)
        sys.exit(1)

    if args.search_only:
        _print_search_only(index_dir, args.query, args.top_k)
        return

    agent = create_agent(index_dir=index_dir, repo_root=Path(".").resolve())
    initial_state = {
        "query": args.query,
        "top_k": max(1, args.top_k),
        "max_retries": max(0, args.max_retries),
        "trace": bool(args.trace),
        "retrieval_attempts": 0,
        "candidates": [],
        "execution_results": [],
        "recovery_path": [],
        "adopted_tools": [],
        "unmet": [],
        "error": None,
        "final_answer": "",
    }

    result = agent.invoke(initial_state)
    if args.trace:
        print("TRACE:")
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        print("")

    print(result.get("final_answer", "(no answer)"))


if __name__ == "__main__":
    main()
