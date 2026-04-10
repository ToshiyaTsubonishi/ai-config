"""Cloud Run selector-serving entrypoint."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from ai_config.mcp_server.runtime import RuntimeIndexStatus, validate_runtime_index
from ai_config.mcp_server.server import create_server
from ai_config.mcp_server.tools import ToolIndex
from ai_config.registry.index_builder import DEFAULT_INDEX_DIR
from ai_config.runtime_env import load_runtime_env

logger = logging.getLogger(__name__)


def _default_port() -> int:
    value = os.getenv("PORT", "8080")
    try:
        return int(value)
    except ValueError:
        return 8080


def _register_runtime_routes(mcp: object, readiness: RuntimeIndexStatus, tool_index: ToolIndex) -> None:
    @mcp.custom_route("/healthz", methods=["GET"], include_in_schema=False)  # type: ignore[attr-defined]
    async def healthz(_request: Request) -> Response:
        return JSONResponse({"status": "ok"})

    @mcp.custom_route("/readyz", methods=["GET"], include_in_schema=False)  # type: ignore[attr-defined]
    async def readyz(_request: Request) -> Response:
        return JSONResponse(readiness.to_readiness_payload())

    @mcp.custom_route("/catalog/tool-detail", methods=["GET"], include_in_schema=False)  # type: ignore[attr-defined]
    async def tool_detail(request: Request) -> Response:
        tool_id = (request.query_params.get("tool_id") or "").strip()
        if not tool_id:
            return JSONResponse(
                {
                    "status": "error",
                    "error": {
                        "code": "MISSING_TOOL_ID",
                        "message": "tool_id query parameter is required.",
                    },
                },
                status_code=400,
            )

        detail = tool_index.get_detail(tool_id)
        if detail is None:
            return JSONResponse(
                {
                    "status": "error",
                    "error": {
                        "code": "TOOL_NOT_FOUND",
                        "message": f"Tool '{tool_id}' not found.",
                    },
                },
                status_code=404,
            )

        return JSONResponse({"status": "success", "tool": detail})


def main(argv: list[str] | None = None) -> None:
    load_runtime_env()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(description="Cloud Run selector-serving MCP entrypoint")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Repository root path",
    )
    parser.add_argument(
        "--index-dir",
        type=Path,
        default=None,
        help=f"Index directory (default: <repo-root>/{DEFAULT_INDEX_DIR})",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Bind host for selector-serving (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=_default_port(),
        help="Bind port for selector-serving (default: PORT env or 8080)",
    )
    parser.add_argument(
        "--streamable-http-path",
        default="/mcp",
        help="Path for streamable HTTP MCP endpoint (default: /mcp)",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    index_dir = (args.index_dir or repo_root / DEFAULT_INDEX_DIR).resolve()

    try:
        readiness = validate_runtime_index(index_dir)
    except Exception as error:
        logger.error("Selector serving startup failed: %s", error)
        sys.exit(1)

    logger.info("Starting selector-serving in read-only runtime mode")
    logger.info("Repo root: %s", repo_root)
    logger.info("Index dir: %s", index_dir)
    logger.info("Transport: streamable-http")
    logger.info("HTTP path: %s", args.streamable_http_path)

    tool_index = ToolIndex(index_dir)
    mcp = create_server(
        index_dir=index_dir,
        repo_root=repo_root,
        include_extended_tools=False,
        host=args.host,
        port=args.port,
        streamable_http_path=args.streamable_http_path,
        stateless_http=True,
    )
    _register_runtime_routes(mcp, readiness, tool_index)
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
