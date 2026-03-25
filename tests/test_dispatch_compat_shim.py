from __future__ import annotations

import sys
from pathlib import Path

from ai_config.dispatch import _compat


def test_load_external_module_uses_sibling_checkout(tmp_path: Path, monkeypatch) -> None:
    external_src = tmp_path / "ai-config-dispatch" / "src"
    package_dir = external_src / "ai_config_dispatch"
    package_dir.mkdir(parents=True)
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "dummy.py").write_text("VALUE = 7\n", encoding="utf-8")

    monkeypatch.setattr(_compat, "_EXTERNAL_REPO_SRC", external_src)
    monkeypatch.setattr(sys, "path", [p for p in sys.path if p != str(external_src)])
    sys.modules.pop("ai_config_dispatch", None)
    sys.modules.pop("ai_config_dispatch.dummy", None)

    module = _compat.load_external_module("dummy")

    assert module.VALUE == 7
    assert str(external_src) in sys.path
