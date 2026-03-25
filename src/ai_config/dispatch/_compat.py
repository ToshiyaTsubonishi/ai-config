"""Compatibility helpers for the external dispatch package."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType

_AI_CONFIG_REPO_ROOT = Path(__file__).resolve().parents[3]
_EXTERNAL_REPO_SRC = _AI_CONFIG_REPO_ROOT.parent / "ai-config-dispatch" / "src"


def _ensure_external_repo_on_path() -> None:
    if not _EXTERNAL_REPO_SRC.exists():
        return
    external_src = str(_EXTERNAL_REPO_SRC)
    if external_src not in sys.path:
        sys.path.insert(0, external_src)


def load_external_module(module_name: str) -> ModuleType:
    """Load a dispatch runtime module from the external package."""

    _ensure_external_repo_on_path()
    target = f"ai_config_dispatch.{module_name}"
    try:
        return importlib.import_module(target)
    except ModuleNotFoundError as exc:
        if exc.name not in {"ai_config_dispatch", target}:
            raise
        raise ImportError(
            "Dispatch runtime moved to the external 'ai-config-dispatch' package. "
            "Install it or clone ../ai-config-dispatch next to this checkout."
        ) from exc
