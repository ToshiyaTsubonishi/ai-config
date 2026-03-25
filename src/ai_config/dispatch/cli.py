"""Compatibility CLI shim for the external dispatch runtime package."""

from __future__ import annotations

from ai_config.dispatch._compat import load_external_module

_external = load_external_module("cli")


def __getattr__(name: str) -> object:
    return getattr(_external, name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(dir(_external)))


def main(argv: list[str] | None = None) -> None:
    _external.main(argv)


if __name__ == "__main__":
    main()
