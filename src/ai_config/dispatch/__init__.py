"""Deprecated compatibility import shim for the external dispatch runtime package."""

from __future__ import annotations

from typing import Any

from ai_config.dispatch._compat import load_external_module


def create_dispatch_agent(*args: Any, **kwargs: Any) -> Any:
    return load_external_module("graph").create_dispatch_agent(*args, **kwargs)

__all__ = ["create_dispatch_agent"]
