from __future__ import annotations

from pathlib import Path

from ai_config.registry.script_parser import scan_skill_scripts


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_scan_skill_scripts_extracts_docstrings_and_skips_non_targets(tmp_path: Path) -> None:
    _write(
        tmp_path / "skills" / "codex" / "demo-skill" / "scripts" / "tool.py",
        '"""Python tool doc."""\n\ndef main():\n    """unused"""\n    return 1\n',
    )
    _write(
        tmp_path / "skills" / "codex" / "demo-skill" / "scripts" / "helper.ps1",
        "<#\n.SYNOPSIS\nPowerShell helper doc\n#>\nWrite-Host 'ok'\n",
    )
    _write(
        tmp_path / "skills" / "codex" / "demo-skill" / "scripts" / "run.sh",
        "# shell helper doc\n# second line\n\necho hi\n",
    )
    _write(
        tmp_path / "skills" / "codex" / "demo-skill" / "scripts" / "cli.ts",
        "/**\n * TypeScript helper doc\n */\nconsole.log('x')\n",
    )

    # Should be excluded by extension.
    _write(
        tmp_path / "skills" / "codex" / "demo-skill" / "scripts" / "schema.xsd",
        "<schema></schema>",
    )

    records = scan_skill_scripts(tmp_path)
    assert len(records) == 4

    by_path = {r.source_path: r for r in records}
    assert any("tool.py" in p for p in by_path)
    assert any("helper.ps1" in p for p in by_path)
    assert any("run.sh" in p for p in by_path)
    assert any("cli.ts" in p for p in by_path)

    py_record = next(r for r in records if r.source_path.endswith("tool.py"))
    assert py_record.description.startswith("Python tool doc")
    assert py_record.tool_kind == "skill_script"
    assert py_record.invoke["backend"] == "skill_script"

