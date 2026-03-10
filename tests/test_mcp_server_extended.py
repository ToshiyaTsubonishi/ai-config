from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import anyio
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from ai_config.mcp_server.downstream_client import DownstreamMCPClient
from ai_config.registry.index_builder import build_index
from ai_config.registry.models import ToolRecord


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _downstream_server_script(path: Path) -> None:
    _write(
        path,
        """from mcp.server.fastmcp import FastMCP

mcp = FastMCP("dummy-downstream")

@mcp.tool()
def echo(message: str) -> str:
    return f"dummy:{message}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
""",
    )


def _echo_script(path: Path) -> None:
    _write(
        path,
        """import sys

print("script-ok:" + " ".join(sys.argv[1:]))
""",
    )


def _shell_echo_args(text: str) -> tuple[str, list[str]]:
    if os.name == "nt":
        return "cmd", ["/c", "echo", text]
    return "sh", ["-lc", f"echo {text}"]


def _toolchain_record() -> ToolRecord:
    return ToolRecord(
        id="toolchain:codex",
        name="codex",
        description="Codex adapter",
        source_path="src/ai_config/executor/adapters/codex.py",
        tool_kind="toolchain_adapter",
        metadata={"enabled_targets": ["codex"], "executable": True},
        tags=["target:codex", "capability:cli_execution"],
        invoke={"backend": "cli", "command": "codex", "args": [], "timeout_ms": 1000, "env_keys": []},
    )


def _build_records(repo_root: Path) -> list[ToolRecord]:
    skill_path = repo_root / "skills" / "shared" / "demo" / "SKILL.md"
    script_path = repo_root / "scripts" / "echo_script.py"
    downstream_path = repo_root / "scripts" / "dummy_downstream.py"

    _write(skill_path, "---\nname: demo\ndescription: demo skill\n---\n# Demo\n")
    _echo_script(script_path)
    _downstream_server_script(downstream_path)
    script_command, script_args = _shell_echo_args("script-ok")

    return [
        ToolRecord(
            id="skill:demo",
            name="demo",
            description="Demo skill",
            source_path=skill_path.relative_to(repo_root).as_posix(),
            tool_kind="skill",
            metadata={"executable": True},
            invoke={"backend": "skill_markdown", "command": skill_path.relative_to(repo_root).as_posix(), "args": [], "timeout_ms": 1000, "env_keys": []},
        ),
        ToolRecord(
            id="skill_script:echo",
            name="echo",
            description="Echo script",
            source_path=script_path.relative_to(repo_root).as_posix(),
            tool_kind="skill_script",
            metadata={"executable": True},
            invoke={"backend": "script", "command": script_command, "args": script_args, "timeout_ms": 10000, "env_keys": []},
        ),
        ToolRecord(
            id="mcp:dummy",
            name="dummy",
            description="Dummy downstream MCP",
            source_path=downstream_path.relative_to(repo_root).as_posix(),
            tool_kind="mcp_server",
            metadata={"transport": "stdio", "executable": True},
            invoke={"backend": "mcp", "command": sys.executable, "args": [downstream_path.relative_to(repo_root).as_posix()], "timeout_ms": 10000, "env_keys": []},
        ),
        _toolchain_record(),
    ]


async def _selector_call(repo_root: Path, index_dir: Path, env: dict[str, str]) -> dict[str, object]:
    toolchain_command, toolchain_args = _shell_echo_args("toolchain-ok")
    env["AI_CONFIG_CODEX_CMD"] = toolchain_command
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "ai_config.mcp_server.server", "--repo-root", str(repo_root), "--index-dir", str(index_dir)],
        env=env,
        cwd=repo_root,
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            tool_names = [tool.name for tool in tools.tools]
            skill_result = await session.call_tool("execute_registry_tool", {"tool_id": "skill:demo"})
            script_result = await session.call_tool("execute_registry_tool", {"tool_id": "skill_script:echo"})
            toolchain_result = await session.call_tool(
                "execute_registry_tool",
                {"tool_id": "toolchain:codex", "params": {"args": toolchain_args}},
            )
            listed = await session.call_tool("list_mcp_server_tools", {"tool_id": "mcp:dummy"})
            called = await session.call_tool(
                "call_mcp_server_tool",
                {"tool_id": "mcp:dummy", "tool_name": "echo", "arguments": {"message": "hi"}},
            )
            return {
                "tool_names": tool_names,
                "skill_result": json.loads(skill_result.content[0].text),
                "script_result": json.loads(script_result.content[0].text),
                "toolchain_result": json.loads(toolchain_result.content[0].text),
                "listed": json.loads(listed.content[0].text),
                "called": json.loads(called.content[0].text),
            }


def test_downstream_client_lists_and_calls_local_dummy_server(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    downstream_path = repo_root / "scripts" / "dummy_downstream.py"
    _downstream_server_script(downstream_path)

    record = ToolRecord(
        id="mcp:dummy",
        name="dummy",
        description="Dummy downstream MCP",
        source_path=downstream_path.relative_to(repo_root).as_posix(),
        tool_kind="mcp_server",
        metadata={"transport": "stdio", "executable": True},
        invoke={"backend": "mcp", "command": sys.executable, "args": [downstream_path.relative_to(repo_root).as_posix()], "timeout_ms": 10000, "env_keys": []},
    )

    client = DownstreamMCPClient(repo_root=repo_root)
    listed = client.list_tools(record)
    names = [tool["name"] for tool in listed["tools"]]
    assert "echo" in names

    called = client.call_tool(record, "echo", {"message": "hello"})
    result = called["result"]
    assert result["isError"] is False
    assert "dummy:hello" in result["content"][0]["text"]


def test_selector_server_exposes_extended_tools_and_executes_records(monkeypatch, tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    (repo_root / "config" / "master").mkdir(parents=True, exist_ok=True)
    _write(repo_root / "config" / "master" / "ai-sync.yaml", "targets: {}\nmcp_servers: {}\n")
    records = _build_records(repo_root)
    index_dir = tmp_path / "index"
    build_index(records, index_dir, embedding_backend="hash", vector_backend="numpy")

    project_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    py_path = str(project_root / "src")
    env["PYTHONPATH"] = py_path if not env.get("PYTHONPATH") else f"{py_path}{os.pathsep}{env['PYTHONPATH']}"
    monkeypatch.setenv("AI_CONFIG_CODEX_CMD", _shell_echo_args("toolchain-ok")[0])

    payload = anyio.run(_selector_call, repo_root, index_dir, env)
    tool_names = set(payload["tool_names"])
    assert {
        "search_tools",
        "get_tool_detail",
        "list_categories",
        "get_tool_count",
        "execute_registry_tool",
        "list_mcp_server_tools",
        "call_mcp_server_tool",
    }.issubset(tool_names)

    assert payload["skill_result"]["status"] == "success"
    assert "content_preview" in payload["skill_result"]["output"]
    assert payload["script_result"]["status"] == "success"
    assert "script-ok" in payload["script_result"]["output"]["stdout"].lower()
    assert payload["toolchain_result"]["status"] == "success"
    assert "toolchain-ok" in payload["toolchain_result"]["output"]["stdout"].lower()

    listed = payload["listed"]
    assert listed["status"] == "success"
    assert listed["output"]["tools"][0]["name"] == "echo"

    called = payload["called"]
    assert called["status"] == "success"
    assert called["output"]["result"]["isError"] is False
    assert "dummy:hi" in called["output"]["result"]["content"][0]["text"]
