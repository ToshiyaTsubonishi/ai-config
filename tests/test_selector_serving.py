from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import anyio
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from ai_config.registry.index_builder import build_index
from ai_config.registry.models import ToolRecord


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _project_env() -> dict[str, str]:
    project_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    py_path = str(project_root / "src")
    env["PYTHONPATH"] = py_path if not env.get("PYTHONPATH") else f"{py_path}{os.pathsep}{env['PYTHONPATH']}"
    return env


def _build_repo(repo_root: Path) -> None:
    repo_root.mkdir(parents=True, exist_ok=True)
    _write(repo_root / "config" / "master" / "ai-sync.yaml", "targets: {}\nmcp_servers: {}\n")
    _write(
        repo_root / "skills" / "shared" / "demo-selector" / "SKILL.md",
        "---\nname: demo-selector\ndescription: selector-serving demo skill\n---\n# Demo\n",
    )


def _build_valid_index(repo_root: Path, index_dir: Path) -> None:
    build_index(
        [
            ToolRecord(
                id="skill:demo-selector",
                name="demo-selector",
                description="Selector serving demo skill",
                source_path="skills/shared/demo-selector/SKILL.md",
                tool_kind="skill",
                metadata={"layer": "shared"},
                tags=["layer:shared"],
            )
        ],
        index_dir,
        embedding_backend="hash",
        vector_backend="numpy",
        profile="default",
    )


def _start_selector_serving(repo_root: Path, index_dir: Path, port: int) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "ai_config.mcp_server.serving",
            "--repo-root",
            str(repo_root),
            "--index-dir",
            str(index_dir),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--streamable-http-path",
            "/mcp",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=_project_env(),
    )


def _wait_for_json(url: str, proc: subprocess.Popen[str], *, timeout: float = 10.0) -> dict[str, object]:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            output = proc.stdout.read() if proc.stdout is not None else ""
            raise AssertionError(f"Server exited before becoming ready:\n{output}")
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.1)
    output = proc.stdout.read() if proc.stdout is not None else ""
    raise AssertionError(f"Timed out waiting for {url}:\n{output}")


def _terminate(proc: subprocess.Popen[str]) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=10)


def _failure_output(result: subprocess.CompletedProcess[str]) -> str:
    return (result.stdout or "") + (result.stderr or "")


async def _selector_serving_call(port: int) -> dict[str, object]:
    async with streamable_http_client(f"http://127.0.0.1:{port}/mcp") as (read, write, _get_session_id):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            search = await session.call_tool("search_tools", {"query": "selector serving demo", "top_k": 3})
            detail = await session.call_tool("get_tool_detail", {"tool_id": "skill:demo-selector"})
            return {
                "tool_names": [tool.name for tool in tools.tools],
                "search": json.loads(search.content[0].text),
                "detail": json.loads(detail.content[0].text),
            }


def test_selector_serving_exposes_read_only_http_mcp_and_health_endpoints(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _build_repo(repo_root)
    index_dir = tmp_path / "index"
    _build_valid_index(repo_root, index_dir)

    port = _free_port()
    proc = _start_selector_serving(repo_root, index_dir, port)
    try:
        health = _wait_for_json(f"http://127.0.0.1:{port}/healthz", proc)
        readiness = _wait_for_json(f"http://127.0.0.1:{port}/readyz", proc)
        catalog = _wait_for_json(f"http://127.0.0.1:{port}/catalog/tool-detail?tool_id=skill:demo-selector", proc)
        payload = anyio.run(_selector_serving_call, port)
    finally:
        _terminate(proc)

    assert health == {"status": "ok"}
    assert readiness["status"] == "ready"
    assert readiness["surface"] == "selector-serving"
    assert readiness["runtime_mode"] == "read_only"
    assert readiness["record_count"] == 1
    assert readiness["index_format_version"] == 4
    assert readiness["profile"] == "default"
    assert readiness["index_dir"] == str(index_dir.resolve())
    assert "summary.json" in readiness["required_artifacts"]
    assert catalog["status"] == "success"
    assert catalog["tool"]["id"] == "skill:demo-selector"
    assert catalog["tool"]["source_path"] == "skills/shared/demo-selector/SKILL.md"

    assert set(payload["tool_names"]) == {
        "search_tools",
        "get_tool_detail",
        "list_categories",
        "get_tool_count",
    }
    assert payload["search"]["count"] == 1
    assert payload["search"]["results"][0]["id"] == "skill:demo-selector"
    assert payload["detail"]["id"] == "skill:demo-selector"


def test_selector_serving_fails_fast_when_index_dir_missing(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _build_repo(repo_root)
    index_dir = tmp_path / "missing-index"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ai_config.mcp_server.serving",
            "--repo-root",
            str(repo_root),
            "--index-dir",
            str(index_dir),
        ],
        capture_output=True,
        text=True,
        env=_project_env(),
        timeout=10,
    )

    output = _failure_output(result)
    assert result.returncode != 0
    assert "Missing required index artifacts for runtime serving" in output
    assert "sync-manifest" not in output
    assert "ai-config-index" not in output


def test_selector_serving_fails_fast_when_required_artifact_missing(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _build_repo(repo_root)
    index_dir = tmp_path / "index"
    _build_valid_index(repo_root, index_dir)
    (index_dir / "keyword_index.json").unlink()

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ai_config.mcp_server.serving",
            "--repo-root",
            str(repo_root),
            "--index-dir",
            str(index_dir),
        ],
        capture_output=True,
        text=True,
        env=_project_env(),
        timeout=10,
    )

    output = _failure_output(result)
    assert result.returncode != 0
    assert "keyword_index.json" in output
    assert "sync-manifest" not in output
    assert "ai-config-index" not in output


def test_selector_serving_fails_fast_when_index_contract_invalid(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _build_repo(repo_root)
    index_dir = tmp_path / "index"
    _build_valid_index(repo_root, index_dir)

    summary_path = index_dir / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["index_format_version"] = 2
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ai_config.mcp_server.serving",
            "--repo-root",
            str(repo_root),
            "--index-dir",
            str(index_dir),
        ],
        capture_output=True,
        text=True,
        env=_project_env(),
        timeout=10,
    )

    output = _failure_output(result)
    assert result.returncode != 0
    assert "Unsupported index_format_version=2" in output
    assert "sync-manifest" not in output
    assert "ai-config-index" not in output
