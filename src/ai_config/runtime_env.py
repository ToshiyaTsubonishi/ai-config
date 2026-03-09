"""Runtime environment loading helpers."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv


def _project_env_file(module_file: str | Path | None = None) -> Path:
    """Return repo-level .env path from this package location."""
    module_path = Path(module_file).resolve() if module_file is not None else Path(__file__).resolve()
    return module_path.parents[2] / ".env"


def _load_if_exists(path: Path) -> Path | None:
    if not path.exists():
        return None
    load_dotenv(path, override=False)
    return path.resolve()


def _ensure_api_key_aliases() -> None:
    """Bridge GOOGLE_API_KEY and GEMINI_API_KEY when only one is set."""
    google_key = os.getenv("GOOGLE_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if google_key and not gemini_key:
        os.environ["GEMINI_API_KEY"] = google_key
    elif gemini_key and not google_key:
        os.environ["GOOGLE_API_KEY"] = gemini_key


def load_runtime_env(*, module_file: str | Path | None = None) -> list[Path]:
    """Load .env from explicit path, cwd ancestry, and repo root (non-overriding)."""
    loaded: list[Path] = []
    seen: set[Path] = set()

    def _load(path: Path) -> None:
        resolved = _load_if_exists(path)
        if resolved is not None and resolved not in seen:
            seen.add(resolved)
            loaded.append(resolved)

    explicit_path = os.getenv("AI_CONFIG_ENV_FILE")
    if explicit_path:
        _load(Path(explicit_path).expanduser())

    cwd_env = find_dotenv(filename=".env", usecwd=True)
    if cwd_env:
        _load(Path(cwd_env))

    _load(_project_env_file(module_file))
    _ensure_api_key_aliases()
    return loaded
