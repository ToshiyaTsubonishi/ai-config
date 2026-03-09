from __future__ import annotations

import os
from pathlib import Path

from ai_config.runtime_env import load_runtime_env


def _module_stub(tmp_path: Path) -> Path:
    module_file = tmp_path / "repo" / "src" / "ai_config" / "runtime_env.py"
    module_file.parent.mkdir(parents=True, exist_ok=True)
    module_file.write_text("# test stub\n", encoding="utf-8")
    return module_file


def test_loads_repo_env_when_cwd_env_missing(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    env_file = repo_root / ".env"
    env_file.write_text(
        "GOOGLE_API_KEY=repo-key\nGEMINI_MODEL=gemini-flash-latest\n",
        encoding="utf-8",
    )

    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    monkeypatch.chdir(work_dir)

    loaded = load_runtime_env(module_file=_module_stub(tmp_path))

    assert os.getenv("GOOGLE_API_KEY") == "repo-key"
    assert os.getenv("GEMINI_API_KEY") == "repo-key"
    assert os.getenv("GEMINI_MODEL") == "gemini-flash-latest"
    assert env_file.resolve() in loaded


def test_does_not_override_existing_env_values(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    env_file = repo_root / ".env"
    env_file.write_text("GOOGLE_API_KEY=repo-key\n", encoding="utf-8")

    monkeypatch.setenv("GOOGLE_API_KEY", "existing-key")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    monkeypatch.chdir(work_dir)

    load_runtime_env(module_file=_module_stub(tmp_path))

    assert os.getenv("GOOGLE_API_KEY") == "existing-key"
    assert os.getenv("GEMINI_API_KEY") == "existing-key"


def test_backfills_google_key_from_gemini_key(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-only-key")
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    monkeypatch.chdir(work_dir)

    load_runtime_env(module_file=_module_stub(tmp_path))

    assert os.getenv("GOOGLE_API_KEY") == "gemini-only-key"
