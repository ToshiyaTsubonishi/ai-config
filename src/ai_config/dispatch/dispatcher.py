"""Compatibility shim for the external dispatch dispatcher module."""

from __future__ import annotations

from ai_config.dispatch._compat import load_external_module

_external = load_external_module("dispatcher")


def __getattr__(name: str) -> object:
    return getattr(_external, name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(dir(_external)))
