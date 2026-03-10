"""Run an ai_config module with repo-local sources and venv dependencies."""

from __future__ import annotations

import runpy
import site
import sys
from pathlib import Path


def _expected_version(repo_root: Path) -> tuple[int, int] | None:
    config_path = repo_root / ".venv" / "pyvenv.cfg"
    if not config_path.exists():
        return None
    for line in config_path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("version"):
            continue
        _, _, raw_value = line.partition("=")
        parts = raw_value.strip().split(".")
        if len(parts) < 2:
            return None
        try:
            return int(parts[0]), int(parts[1])
        except ValueError:
            return None
    return None


def main() -> int:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: run_module.py <module> [args...]")

    module = sys.argv[1]
    repo_root = Path(__file__).resolve().parents[1]
    expected_version = _expected_version(repo_root)
    if expected_version and sys.version_info[:2] != expected_version:
        expected_text = ".".join(str(part) for part in expected_version)
        actual_text = f"{sys.version_info.major}.{sys.version_info.minor}"
        raise SystemExit(
            f"Python {expected_text} is required for {repo_root / '.venv'}, "
            f"but the fallback interpreter is {actual_text}."
        )

    src_dir = repo_root / "src"
    site_packages = repo_root / ".venv" / "Lib" / "site-packages"
    if not src_dir.exists():
        raise SystemExit(f"Repository source directory is missing: {src_dir}")
    if not site_packages.exists():
        raise SystemExit(f"Virtualenv site-packages directory is missing: {site_packages}")

    sys.path.insert(0, str(src_dir))
    site.addsitedir(str(site_packages))
    sys.argv = [module, *sys.argv[2:]]
    runpy.run_module(module, run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
