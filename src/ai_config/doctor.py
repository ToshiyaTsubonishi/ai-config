"""Environment and runtime verification CLI for ai-config."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from datetime import datetime
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator

import anyio
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from ai_config.runtime_env import load_runtime_env
from ai_config.vendor.skill_vendor import inspect_vendor_state


@dataclass
class CheckResult:
    name: str
    status: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


def _pass(name: str, message: str, **details: Any) -> CheckResult:
    return CheckResult(name=name, status="pass", message=message, details=details)


def _fail(name: str, message: str, **details: Any) -> CheckResult:
    return CheckResult(name=name, status="fail", message=message, details=details)


def _skip(name: str, message: str, **details: Any) -> CheckResult:
    return CheckResult(name=name, status="skip", message=message, details=details)


def _resolve_command(command: str) -> list[str]:
    resolved = shutil.which(command)
    if resolved:
        return [resolved]
    if os.name == "nt" and "." not in Path(command).name:
        for suffix in (".cmd", ".exe", ".bat", ".ps1"):
            resolved = shutil.which(command + suffix)
            if not resolved:
                continue
            if suffix == ".ps1":
                runner = shutil.which("pwsh") or shutil.which("powershell")
                if runner:
                    return [runner, "-File", resolved]
            return [resolved]
    raise FileNotFoundError(f"Command not found: {command}")


def _run_command(command: list[str], *, cwd: Path | None = None, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    if not command:
        raise ValueError("Command must not be empty.")
    resolved_command = _resolve_command(command[0]) + command[1:]
    return subprocess.run(
        resolved_command,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _trim(text: str, limit: int = 400) -> str:
    raw = text.strip()
    if len(raw) <= limit:
        return raw
    return raw[:limit] + "..."


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _read_json_list(path: Path) -> list[dict[str, Any]] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, list):
        return None
    if not all(isinstance(item, dict) for item in data):
        return None
    return [dict(item) for item in data]


def _file_matches(left: Path, right: Path) -> bool:
    if not left.exists() or not right.exists():
        return False
    return left.read_text(encoding="utf-8") == right.read_text(encoding="utf-8")


def _selector_text_payload(result: Any) -> str:
    content = getattr(result, "content", []) or []
    parts: list[str] = []
    for item in content:
        if hasattr(item, "text"):
            parts.append(str(item.text))
        else:
            parts.append(str(item))
    return "".join(parts).strip()


def _selector_json_payload(result: Any) -> dict[str, Any]:
    return json.loads(_selector_text_payload(result))


@asynccontextmanager
async def _selector_session(repo_root: Path) -> AsyncIterator[ClientSession]:
    # Unix-like: .venv/bin/ai-config-mcp-server
    selector_exe = repo_root / ".venv" / "bin" / "ai-config-mcp-server"
    if not selector_exe.exists():
        # Windows: .venv/Scripts/ai-config-mcp-server.cmd or .exe
        selector_exe = repo_root / ".venv" / "Scripts" / "ai-config-mcp-server.cmd"
        if not selector_exe.exists():
            selector_exe = repo_root / ".venv" / "Scripts" / "ai-config-mcp-server.exe"
    params = StdioServerParameters(
        command=str(selector_exe),
        args=["--repo-root", str(repo_root)],
        env=None,
        cwd=repo_root,
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


async def _run_selector_checks(repo_root: Path) -> list[CheckResult]:
    expected_selector_tools = {
        "search_tools",
        "get_tool_detail",
        "list_categories",
        "get_tool_count",
        "execute_registry_tool",
        "list_mcp_server_tools",
        "call_mcp_server_tool",
    }
    results: list[CheckResult] = []

    try:
        async with _selector_session(repo_root) as session:
            tools = await session.list_tools()
            tool_names = {tool.name for tool in tools.tools}
            if expected_selector_tools.issubset(tool_names):
                results.append(_pass("selector_tools", "Selector MCP exposed expected tools.", tools=sorted(tool_names)))
            else:
                results.append(
                    _fail(
                        "selector_tools",
                        "Selector MCP did not expose the expected tool set.",
                        tools=sorted(tool_names),
                        missing=sorted(expected_selector_tools - tool_names),
                    )
                )

            search_payload = _selector_json_payload(await session.call_tool("search_tools", {"query": "codex dispatch mcp", "top_k": 3}))
            search_count = int(search_payload.get("count", 0))
            if search_count > 0:
                results.append(_pass("selector_search", "Selector MCP search returned candidates.", count=search_count))
            else:
                results.append(_fail("selector_search", "Selector MCP search returned no candidates.", payload=search_payload))

            learn_payload = _selector_json_payload(await session.call_tool("list_mcp_server_tools", {"tool_id": "mcp:microsoft-learn-mcp"}))
            learn_tools = [tool.get("name", "") for tool in learn_payload.get("output", {}).get("tools", [])]
            expected_learn = {"microsoft_docs_search", "microsoft_code_sample_search", "microsoft_docs_fetch"}
            if expected_learn.issubset(set(learn_tools)):
                results.append(_pass("learn_mcp_tools", "Microsoft Learn downstream MCP listed expected tools.", tools=learn_tools))
            else:
                results.append(_fail("learn_mcp_tools", "Microsoft Learn downstream MCP tool list was incomplete.", tools=learn_tools))

            learn_call = _selector_json_payload(
                await session.call_tool(
                    "call_mcp_server_tool",
                    {
                        "tool_id": "mcp:microsoft-learn-mcp",
                        "tool_name": "microsoft_docs_search",
                        "arguments": {"query": "Azure Functions Python triggers"},
                    },
                )
            )
            learn_result = learn_call.get("output", {}).get("result", {})
            learn_ok = bool(learn_result) and not bool(learn_result.get("isError"))
            if learn_ok:
                results.append(_pass("learn_mcp_call", "Microsoft Learn downstream MCP call succeeded.", result=learn_result))
            else:
                results.append(_fail("learn_mcp_call", "Microsoft Learn downstream MCP call failed.", payload=learn_call))

            fs_payload = _selector_json_payload(await session.call_tool("list_mcp_server_tools", {"tool_id": "mcp:filesystem"}))
            fs_tools = [tool.get("name", "") for tool in fs_payload.get("output", {}).get("tools", [])]
            if {"list_allowed_directories", "list_directory"}.issubset(set(fs_tools)):
                results.append(_pass("filesystem_mcp_tools", "Filesystem downstream MCP listed expected tools.", tools=fs_tools))
            else:
                results.append(_fail("filesystem_mcp_tools", "Filesystem downstream MCP tool list was incomplete.", tools=fs_tools))

            fs_allowed = _selector_json_payload(
                await session.call_tool(
                    "call_mcp_server_tool",
                    {
                        "tool_id": "mcp:filesystem",
                        "tool_name": "list_allowed_directories",
                        "arguments": {},
                    },
                )
            )
            allowed_result = fs_allowed.get("output", {}).get("result", {})
            allowed_text = "\n".join(
                [
                    str(item.get("text", ""))
                    for item in (allowed_result.get("content") or [])
                    if isinstance(item, dict)
                ]
            )
            if not allowed_text:
                structured = allowed_result.get("structuredContent") or {}
                allowed_text = str(structured.get("content", ""))
            if str(repo_root).lower() in allowed_text.lower():
                results.append(_pass("filesystem_allowed_dirs", "Filesystem downstream MCP expanded WORKSPACE_ROOT correctly.", result=allowed_result))
            else:
                results.append(_fail("filesystem_allowed_dirs", "Filesystem downstream MCP did not report the repo root.", payload=fs_allowed))

            fs_list = _selector_json_payload(
                await session.call_tool(
                    "call_mcp_server_tool",
                    {
                        "tool_id": "mcp:filesystem",
                        "tool_name": "list_directory",
                        "arguments": {"path": str(repo_root)},
                    },
                )
            )
            list_result = fs_list.get("output", {}).get("result", {})
            if list_result and not bool(list_result.get("isError")):
                results.append(_pass("filesystem_list_directory", "Filesystem downstream MCP listed the repo directory.", result=list_result))
            else:
                results.append(_fail("filesystem_list_directory", "Filesystem downstream MCP list_directory failed.", payload=fs_list))
    except Exception as error:
        results.append(_fail("selector_runtime", "Selector MCP runtime checks failed.", error=str(error)))

    return results


def _runtime_config_checks(repo_root: Path) -> list[CheckResult]:
    results: list[CheckResult] = []
    home = Path.home()

    codex_config = home / ".codex" / "config.toml"
    gemini_config = home / ".gemini" / "settings.json"
    antigravity_config = home / ".gemini" / "antigravity" / "mcp_config.json"

    if codex_config.exists() and "[mcp_servers.ai-config-selector]" in codex_config.read_text(encoding="utf-8"):
        results.append(_pass("codex_config", "Codex config contains ai-config-selector.", path=str(codex_config)))
    else:
        results.append(_fail("codex_config", "Codex config is missing ai-config-selector.", path=str(codex_config)))

    gemini_data = _read_json(gemini_config)
    if gemini_data and "ai-config-selector" in (gemini_data.get("mcpServers") or {}):
        results.append(_pass("gemini_config", "Gemini settings contain ai-config-selector.", path=str(gemini_config)))
    else:
        results.append(_fail("gemini_config", "Gemini settings are missing ai-config-selector.", path=str(gemini_config)))

    antigravity_data = _read_json(antigravity_config)
    if antigravity_data and "ai-config-selector" in (antigravity_data.get("mcpServers") or {}):
        results.append(_pass("antigravity_config", "Antigravity MCP config contains ai-config-selector.", path=str(antigravity_config)))
    else:
        results.append(_fail("antigravity_config", "Antigravity MCP config is missing ai-config-selector.", path=str(antigravity_config)))

    try:
        codex_list = _run_command(["codex", "mcp", "list"], cwd=repo_root, timeout=20)
        if codex_list.returncode == 0 and "ai-config-selector" in codex_list.stdout:
            results.append(_pass("codex_mcp_list", "Codex CLI listed ai-config-selector.", stdout=_trim(codex_list.stdout)))
        else:
            results.append(_fail("codex_mcp_list", "Codex CLI did not list ai-config-selector.", stdout=_trim(codex_list.stdout), stderr=_trim(codex_list.stderr)))
    except Exception as error:
        results.append(_fail("codex_mcp_list", "Codex CLI registration check failed.", error=str(error)))

    try:
        gemini_list = _run_command(["gemini", "mcp", "list"], cwd=repo_root, timeout=20)
        gemini_output = "\n".join(x for x in [gemini_list.stdout, gemini_list.stderr] if x)
        if gemini_list.returncode == 0 and "ai-config-selector" in gemini_output:
            results.append(_pass("gemini_mcp_list", "Gemini CLI listed ai-config-selector.", output=_trim(gemini_output)))
        else:
            results.append(_fail("gemini_mcp_list", "Gemini CLI did not list ai-config-selector.", stdout=_trim(gemini_list.stdout), stderr=_trim(gemini_list.stderr)))
    except Exception as error:
        results.append(_fail("gemini_mcp_list", "Gemini CLI registration check failed.", error=str(error)))

    return results


def _instruction_checks(repo_root: Path) -> list[CheckResult]:
    home = Path.home()
    pairs = [
        ("codex_instructions", repo_root / "instructions" / "Agent.md", home / ".codex" / "AGENTS.md"),
        ("gemini_instructions", repo_root / "instructions" / "Gemini.md", home / ".gemini" / "GEMINI.md"),
    ]
    results: list[CheckResult] = []
    for name, store, target in pairs:
        if _file_matches(store, target):
            results.append(_pass(name, "Instruction file is synced.", store=str(store), target=str(target)))
        elif not target.exists():
            results.append(_fail(name, "Instruction target file is missing.", store=str(store), target=str(target)))
        else:
            results.append(_fail(name, "Instruction file has drift.", store=str(store), target=str(target)))
    return results


def _dispatch_prereq_checks(repo_root: Path) -> list[CheckResult]:
    results: list[CheckResult] = []
    for name, command in (("codex_cli", "codex"), ("gemini_cli", "gemini"), ("antigravity_cli", "antigravity")):
        try:
            proc = _run_command([command, "--help"], cwd=repo_root, timeout=20)
            if proc.returncode == 0:
                results.append(_pass(name, "CLI is available.", command=command))
            else:
                results.append(_fail(name, "CLI returned a non-zero exit code.", command=command, stderr=_trim(proc.stderr)))
        except Exception as error:
            results.append(_fail(name, "CLI is not available.", command=command, error=str(error)))

    if Path(repo_root / ".env").exists():
        env_text = (repo_root / ".env").read_text(encoding="utf-8")
        for line in env_text.splitlines():
            if line.startswith("GOOGLE_API_KEY="):
                value = line.split("=", 1)[1].strip()
                if value:
                    results.append(_pass("google_api_key", "GOOGLE_API_KEY is configured."))
                else:
                    results.append(_skip("google_api_key", "GOOGLE_API_KEY is empty; LLM planning checks may degrade."))
                break
        else:
            results.append(_skip("google_api_key", "GOOGLE_API_KEY is not declared in .env."))
    else:
        results.append(_skip("google_api_key", ".env is missing."))
    return results


def _vendor_observability_checks(repo_root: Path) -> list[CheckResult]:
    results: list[CheckResult] = []

    try:
        report = inspect_vendor_state(repo_root)
    except Exception as error:
        results.append(_fail("vendor_manifest", "Vendor observability inspection failed.", error=str(error)))
        results.append(_skip("vendor_materialization", "Skipped because vendor inspection failed."))
        results.append(_skip("vendor_git_hygiene", "Skipped because vendor inspection failed."))
        results.append(_skip("vendor_index_presence", "Skipped because vendor inspection failed."))
        results.append(_skip("vendor_extra_local", "Skipped because vendor inspection failed."))
        results.append(_skip("vendor_unmanaged_local", "Skipped because vendor inspection failed."))
        return results

    if report.manifest_errors:
        results.append(
            _fail(
                "vendor_manifest",
                "Vendor manifest is invalid or incomplete.",
                manifest_path=report.manifest_path,
                errors=report.manifest_errors,
            )
        )
    else:
        results.append(
            _pass(
                "vendor_manifest",
                "Vendor manifest is present and fully pinned.",
                manifest_path=report.manifest_path,
                total_manifest_entries=report.summary.total_manifest_entries,
            )
        )

    materialization_problems = [
        entry
        for entry in report.entries
        if entry.is_manifest_managed
        and entry.status in {"needs_align", "needs_sync", "missing", "legacy_submodule", "missing_provenance"}
    ]
    if materialization_problems:
        details = [
            {
                "local_name": entry.local_name,
                "status": entry.status,
                "message": entry.message,
            }
            for entry in materialization_problems
        ]
        remediation = "ai-config-vendor-skills --repo-root . sync-manifest"
        if any(entry.status == "legacy_submodule" for entry in materialization_problems):
            remediation = "ai-config-vendor-skills --repo-root . cleanup-legacy-submodule <local-name> --apply"
        elif any(entry.status == "missing_provenance" for entry in materialization_problems):
            remediation = (
                "Legacy checkout なら bootstrap-legacy、そうでなければ unmanaged local content を確認してください。"
            )
        results.append(
            _fail(
                "vendor_materialization",
                "Vendor-managed external skills need maintenance.",
                remediation=remediation,
                entries=details,
            )
        )
    else:
        results.append(
            _pass(
                "vendor_materialization",
                "Vendor-managed external skills match the pinned manifest state.",
                ready=report.summary.ready,
            )
        )

    gitmodules_exists = (repo_root / ".gitmodules").exists()
    legacy_entries = [entry.local_name for entry in report.entries if entry.status == "legacy_submodule"]
    non_ignored_entries = [
        entry.local_name for entry in report.entries if entry.is_manifest_managed and not entry.git_ignored
    ]
    if gitmodules_exists or legacy_entries or non_ignored_entries:
        results.append(
            _fail(
                "vendor_git_hygiene",
                "Vendor git hygiene checks failed.",
                gitmodules_exists=gitmodules_exists,
                legacy_submodules=legacy_entries,
                not_git_ignored=non_ignored_entries,
            )
        )
    else:
        results.append(_pass("vendor_git_hygiene", "Vendor payloads are local artifacts and git ignored."))

    index_dir = repo_root / ".index"
    summary_path = index_dir / "summary.json"
    records_path = index_dir / "records.json"
    if not summary_path.exists() or not records_path.exists():
        results.append(
            _fail(
                "vendor_index_presence",
                "Index artifacts are missing; rebuild the index.",
                missing=[str(path) for path in (summary_path, records_path) if not path.exists()],
            )
        )
    else:
        records = _read_json_list(records_path)
        external_records = []
        if records is not None:
            external_records = [
                record for record in records if str(record.get("source_path", "")).startswith("skills/external/")
            ]
        if external_records:
            results.append(
                _pass(
                    "vendor_index_presence",
                    "Current index contains external vendor-managed records.",
                    external_record_count=len(external_records),
                )
            )
        else:
            results.append(
                _fail(
                    "vendor_index_presence",
                    "Current index does not contain any skills/external records.",
                    records_path=str(records_path),
                )
            )

    extra_local = [entry.local_name for entry in report.entries if entry.status == "extra_local"]
    if extra_local:
        results.append(
            _pass(
                "vendor_extra_local",
                "Extra local vendor payloads exist outside the curated manifest.",
                entries=extra_local,
            )
        )
    else:
        results.append(_pass("vendor_extra_local", "No extra local vendor payloads were found."))

    unmanaged_local = [entry.local_name for entry in report.entries if entry.status == "unmanaged_local"]
    if unmanaged_local:
        results.append(
            _fail(
                "vendor_unmanaged_local",
                "Unmanaged local external content was found.",
                entries=unmanaged_local,
                remediation=(
                    "意図した local artifact なら managed import に移し、不要なら手動削除してください。"
                ),
            )
        )
    else:
        results.append(_pass("vendor_unmanaged_local", "No unmanaged local external content was found."))

    return results


def _codex_dispatch_check(repo_root: Path) -> CheckResult:
    prompt = (
        "Inspect this repository in read-only mode and verify four areas with evidence: "
        "Windows setup entrypoints, selector MCP registration, downstream MCP execution support, "
        "and instruction sync. Produce a concise report. Do not modify files."
    )
    dispatch_dir = repo_root / ".dispatch"
    dispatch_dir.mkdir(parents=True, exist_ok=True)
    log_path = dispatch_dir / f"codex-doctor-{datetime.now().strftime('%Y%m%d-%H%M%S')}.jsonl"
    try:
        proc = _run_command(
            [
                "codex",
                "exec",
                prompt,
                "--json",
                "--full-auto",
                "-c",
                "shell_environment_policy.inherit=all",
                "--cd",
                str(repo_root),
            ],
            cwd=repo_root,
            timeout=480,
        )
    except subprocess.TimeoutExpired as error:
        partial_stdout = error.stdout or ""
        if isinstance(partial_stdout, bytes):
            partial_stdout = partial_stdout.decode("utf-8", errors="replace")
        if partial_stdout:
            log_path.write_text(partial_stdout, encoding="utf-8")
        return _fail(
            "codex_dispatch_autoroute",
            "Codex dispatch validation timed out.",
            error=str(error),
            log_path=str(log_path),
        )
    except Exception as error:
        return _fail(
            "codex_dispatch_autoroute",
            "Codex dispatch validation could not be executed.",
            error=str(error),
            log_path=str(log_path),
        )

    log_path.write_text(proc.stdout, encoding="utf-8")

    if proc.returncode != 0:
        return _fail(
            "codex_dispatch_autoroute",
            "Codex dispatch validation returned a non-zero exit code.",
            stdout=_trim(proc.stdout, limit=1200),
            stderr=_trim(proc.stderr, limit=1200),
            log_path=str(log_path),
        )

    stdout = proc.stdout
    used_selector = "search_tools" in stdout
    used_dispatch = "ai-config-dispatch" in stdout
    if used_selector and used_dispatch:
        return _pass(
            "codex_dispatch_autoroute",
            "Codex used selector MCP and invoked ai-config-dispatch without an explicit dispatch request.",
            stdout=_trim(stdout, limit=1200),
            log_path=str(log_path),
        )
    return _fail(
        "codex_dispatch_autoroute",
        "Codex did not show both selector MCP usage and ai-config-dispatch invocation.",
        used_selector=used_selector,
        used_dispatch=used_dispatch,
        stdout=_trim(stdout, limit=1200),
        stderr=_trim(proc.stderr, limit=1200),
        log_path=str(log_path),
    )


def run_doctor(repo_root: Path, *, include_codex_dispatch: bool) -> list[CheckResult]:
    results: list[CheckResult] = []
    results.extend(_runtime_config_checks(repo_root))
    results.extend(_instruction_checks(repo_root))
    results.extend(_dispatch_prereq_checks(repo_root))
    results.extend(_vendor_observability_checks(repo_root))
    results.extend(anyio.run(_run_selector_checks, repo_root))
    if include_codex_dispatch:
        results.append(_codex_dispatch_check(repo_root))
    else:
        results.append(_skip("codex_dispatch_autoroute", "Skipped. Re-run with --check-codex-dispatch to execute the black-box validation."))
    return results


def _print_human(results: list[CheckResult]) -> None:
    for item in results:
        print(f"[{item.status}] {item.name}: {item.message}")
        if item.details:
            print(f"  details: {json.dumps(item.details, ensure_ascii=False, default=str)[:800]}")


def main(argv: list[str] | None = None) -> None:
    load_runtime_env()

    parser = argparse.ArgumentParser(description="Verify ai-config environment setup and runtime behavior")
    parser.add_argument("--repo-root", type=Path, default=Path("."), help="Repository root")
    parser.add_argument("--json", action="store_true", help="Print structured JSON output")
    parser.add_argument(
        "--check-codex-dispatch",
        action="store_true",
        help="Run the slower black-box Codex dispatch validation",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    results = run_doctor(repo_root, include_codex_dispatch=args.check_codex_dispatch)

    if args.json:
        print(json.dumps([asdict(item) for item in results], ensure_ascii=False, indent=2, default=str))
    else:
        _print_human(results)

    if any(item.status == "fail" for item in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
