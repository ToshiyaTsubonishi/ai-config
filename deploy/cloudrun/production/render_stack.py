#!/usr/bin/env python3
"""Wrapper around the shared Cloud Run stack renderer for production values."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
STAGING_RENDERER = ROOT.parent / "staging" / "render_stack.py"


def _load_renderer_main():
    spec = importlib.util.spec_from_file_location("staging_render_stack", STAGING_RENDERER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load renderer from {STAGING_RENDERER}")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except ModuleNotFoundError as error:  # pragma: no cover - CLI guard
        if error.name == "yaml":
            raise RuntimeError(
                "PyYAML is required. Run this wrapper with /Users/tsytbns/Documents/GitHub/ai-config/.venv/bin/python "
                "or install pyyaml in the current interpreter."
            ) from error
        raise
    return module.main


def _has_flag(args: list[str], flag: str) -> bool:
    return any(arg == flag or arg.startswith(f"{flag}=") for arg in args)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    forwarded: list[str] = []
    if not _has_flag(args, "--config"):
        forwarded.extend(["--config", str(ROOT / "stack.example.yaml")])
    if not _has_flag(args, "--output-dir"):
        forwarded.extend(["--output-dir", str(ROOT / "rendered")])
    forwarded.extend(args)

    renderer_main = _load_renderer_main()
    return renderer_main(forwarded)


if __name__ == "__main__":
    raise SystemExit(main())
