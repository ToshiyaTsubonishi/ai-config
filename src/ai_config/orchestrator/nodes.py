"""Node implementations for the orchestration graph."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from ai_config.executor import ToolExecutor
from ai_config.orchestrator.candidate_bias import boost_hits
from ai_config.orchestrator.router import (
    SPECIALIST_CANDIDATE_THRESHOLD,
    SPECIALIST_GENERAL,
    route_specialist as decide_specialist,
    specialist_filters,
)
from ai_config.orchestrator.plan_schema import PlanObject, PlanStep, parse_plan_text
from ai_config.retriever.hybrid_search import HybridRetriever
from ai_config.retriever.query_intent import infer_query_intent

logger = logging.getLogger(__name__)

_runtime_index_dir = Path(".index")
_runtime_repo_root = Path(".")
_retriever: HybridRetriever | None = None
_executor: ToolExecutor | None = None
_llm = None


def configure_runtime(index_dir: Path | None = None, repo_root: Path | None = None) -> None:
    global _runtime_index_dir, _runtime_repo_root, _retriever, _executor
    if index_dir is not None:
        _runtime_index_dir = index_dir.resolve()
    if repo_root is not None:
        _runtime_repo_root = repo_root.resolve()
    _retriever = None
    _executor = None


def _get_retriever() -> HybridRetriever:
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever(_runtime_index_dir)
    return _retriever


def _get_executor() -> ToolExecutor:
    global _executor
    if _executor is None:
        _executor = ToolExecutor(repo_root=_runtime_repo_root)
    return _executor


def _get_llm():
    global _llm
    if _llm is not None:
        return _llm

    if not os.getenv("GOOGLE_API_KEY"):
        return None
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except Exception:
        return None

    model_name = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
    _llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.1)
    return _llm


def route_specialist(state: dict[str, Any]) -> dict[str, Any]:
    query = str(state.get("query", ""))
    specialist, score = decide_specialist(query)
    return {
        "specialist": specialist,
        "specialist_score": score,
        "specialist_fallback_used": False,
    }


def _resolve_tool_kinds(intent_kinds: list[str], specialist_kinds: list[str] | None) -> list[str] | None:
    if not specialist_kinds:
        return intent_kinds or None
    if not intent_kinds:
        return specialist_kinds
    intersection = sorted(set(intent_kinds).intersection(specialist_kinds))
    return intersection or intent_kinds


def _retrieve_hits(
    query: str,
    top_k: int,
    specialist: str,
    *,
    executable_only: bool = True,
    strict_intent: bool = True,
) -> tuple[list[Any], dict[str, Any]]:
    intent = infer_query_intent(query)
    filters = specialist_filters(specialist)
    tool_kinds = _resolve_tool_kinds(intent.tool_kinds, filters.get("tool_kinds")) if strict_intent else (filters.get("tool_kinds") or None)
    targets = intent.targets if strict_intent else []
    capabilities = intent.capabilities if strict_intent else []
    retriever = _get_retriever()
    hits = retriever.search(
        query=query,
        top_k=top_k,
        semantic_k=max(top_k * 4, 20),
        bm25_k=max(top_k * 4, 20),
        tool_kinds=tool_kinds or None,
        targets=targets or None,
        capabilities=capabilities or None,
        source_repos=filters.get("source_repos"),
        domains=filters.get("domains"),
        executable_only=executable_only,
    )
    hits = boost_hits(query, hits)
    return hits, {
        "tool_kinds": intent.tool_kinds,
        "targets": intent.targets,
        "capabilities": intent.capabilities,
    }


def retrieve_candidates(state: dict[str, Any]) -> dict[str, Any]:
    query = state["query"]
    top_k = int(state.get("top_k", 8))
    attempt = int(state.get("retrieval_attempts", 0)) + 1
    specialist = str(state.get("specialist") or SPECIALIST_GENERAL)
    specialist_score = float(state.get("specialist_score", 0.0))
    specialist_fallback_used = bool(state.get("specialist_fallback_used", False))

    hits, intent_payload = _retrieve_hits(query, top_k, specialist, executable_only=True)
    active_specialist = specialist
    if (
        specialist != SPECIALIST_GENERAL
        and len(hits) < SPECIALIST_CANDIDATE_THRESHOLD
        and not specialist_fallback_used
    ):
        fallback_hits, fallback_intent = _retrieve_hits(query, top_k, SPECIALIST_GENERAL, executable_only=True)
        if fallback_hits:
            hits = fallback_hits
            intent_payload = fallback_intent
            specialist_fallback_used = True
            active_specialist = SPECIALIST_GENERAL
            specialist_score = 0.0

    candidates = [hit.to_dict() for hit in hits]
    logger.info(
        "retrieve_candidates: query=%r candidates=%d attempt=%d specialist=%s",
        query[:80],
        len(candidates),
        attempt,
        active_specialist,
    )
    return {
        "candidates": candidates,
        "intent": intent_payload,
        "retrieval_attempts": attempt,
        "require_reretrieve": False,
        "reretrieve_failed": False,
        "specialist": active_specialist,
        "specialist_score": specialist_score,
        "specialist_fallback_used": specialist_fallback_used,
        "error": None,
    }


_PLAN_PROMPT = """\
あなたは厳格な実行計画エンジンです。必ず JSON のみ返してください。

ユーザー要求:
{query}

候補ツール:
{candidates}

制約:
- steps は実行順に並べる
- 各 step は step_id/tool_id/action/reason/params を含める
- action は "run" を基本にする
- 候補外の tool_id を作らない

返却 JSON 形式:
{{
  "steps": [
    {{
      "step_id": "step-1",
      "tool_id": "...",
      "action": "run",
      "reason": "...",
      "params": {{}}
    }}
  ],
  "feasibility": "full|partial|impossible",
  "notes": "..."
}}
"""


def _fallback_plan(query: str, candidates: list[dict[str, Any]]) -> PlanObject:
    if not candidates:
        return PlanObject(steps=[], feasibility="impossible", notes="No candidates retrieved.")

    first = candidates[0]
    params: dict[str, Any] = {}
    if first.get("tool_kind") == "toolchain_adapter":
        params = {"args": ["--help"]}
    step = PlanStep(
        step_id="step-1",
        tool_id=str(first["id"]),
        action="run",
        reason=f"Top-ranked candidate for query: {query[:80]}",
        params=params,
    )
    return PlanObject(steps=[step], feasibility="partial", notes="Heuristic fallback planner used.")


def plan_steps(state: dict[str, Any]) -> dict[str, Any]:
    query = state["query"]
    candidates = state.get("candidates", [])

    llm = _get_llm()
    if not llm:
        plan_obj = _fallback_plan(query, candidates)
    else:
        prompt = _PLAN_PROMPT.format(
            query=query,
            candidates=json.dumps(
                [
                    {
                        "id": c.get("id"),
                        "name": c.get("name"),
                        "tool_kind": c.get("tool_kind"),
                        "description": c.get("description"),
                        "score": c.get("score"),
                    }
                    for c in candidates
                ],
                ensure_ascii=False,
                indent=2,
            ),
        )
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, str):
                    parts.append(part)
                elif hasattr(part, "text"):
                    parts.append(part.text)
                else:
                    parts.append(str(part))
            content = "".join(parts)
        plan_obj = parse_plan_text(content)
        if not plan_obj.steps and candidates:
            plan_obj = _fallback_plan(query, candidates)

    logger.info("plan_steps: steps=%d feasibility=%s", len(plan_obj.steps), plan_obj.feasibility)
    return {
        "plan": plan_obj.model_dump(),
        "current_step": 0,
        "step_retry_count": 0,
        "done": len(plan_obj.steps) == 0,
        "needs_repair": False,
        "require_reretrieve": False,
    }


def _current_plan(state: dict[str, Any]) -> PlanObject:
    raw = state.get("plan") or {}
    try:
        return PlanObject.model_validate(raw)
    except Exception:
        return PlanObject(steps=[], feasibility="impossible", notes="Plan is invalid.")


def execute_step(state: dict[str, Any]) -> dict[str, Any]:
    plan = _current_plan(state)
    idx = int(state.get("current_step", 0))
    if idx >= len(plan.steps):
        return {"done": True, "last_step_result": None}

    step = plan.steps[idx]
    candidates = state.get("candidates", [])
    executor = _get_executor()
    executor.register_records(candidates)
    result = executor.tools_call(
        tool_id=step.tool_id,
        action=step.action,
        params=step.params,
        cwd=step.working_directory,
    )

    execution_results = list(state.get("execution_results", []))
    step_result = {
        "step_id": step.step_id,
        "step_index": idx,
        "tool_id": step.tool_id,
        "action": step.action,
        "status": result.get("status", "error"),
        "output": result.get("output"),
        "error": result.get("error"),
    }
    execution_results.append(step_result)

    adopted_tools = list(state.get("adopted_tools", []))
    if step_result["status"] == "success":
        adopted_tools.append(step.tool_id)

    logger.info("execute_step: idx=%d tool=%s status=%s", idx, step.tool_id, step_result["status"])
    return {
        "execution_results": execution_results,
        "last_step_result": step_result,
        "adopted_tools": adopted_tools,
    }


def evaluate_step(state: dict[str, Any]) -> dict[str, Any]:
    plan = _current_plan(state)
    idx = int(state.get("current_step", 0))
    last = state.get("last_step_result")

    if idx >= len(plan.steps) or not last:
        return {"done": True, "needs_repair": False}

    if last.get("status") == "success":
        next_idx = idx + 1
        done = next_idx >= len(plan.steps)
        return {"current_step": next_idx, "done": done, "needs_repair": False, "step_retry_count": 0}

    return {"done": False, "needs_repair": True}


def repair_or_fallback(state: dict[str, Any]) -> dict[str, Any]:
    if not state.get("needs_repair"):
        return {}

    plan = _current_plan(state)
    idx = int(state.get("current_step", 0))
    if idx >= len(plan.steps):
        return {"abort": True, "done": True}
    step = plan.steps[idx]

    step_retry_count = int(state.get("step_retry_count", 0))
    recovery = list(state.get("recovery_path", []))

    if step_retry_count < 1:
        recovery.append(f"retry_same_step:{step.step_id}")
        return {"step_retry_count": step_retry_count + 1, "needs_repair": False, "recovery_path": recovery}

    candidates = state.get("candidates", [])
    alt_tool = None
    for c in candidates:
        candidate_id = str(c.get("id", ""))
        if candidate_id and candidate_id != step.tool_id:
            alt_tool = candidate_id
            break

    if alt_tool:
        step.tool_id = alt_tool
        step.reason = (step.reason + " | repaired via alternative candidate").strip()
        plan.steps[idx] = step
        recovery.append(f"repair_alternative:{step.step_id}:{alt_tool}")
        return {
            "plan": plan.model_dump(),
            "step_retry_count": 0,
            "needs_repair": False,
            "recovery_path": recovery,
        }

    unmet = list(state.get("unmet", []))
    unmet.append(f"Step {step.step_id} failed and no local alternative candidate was found.")
    recovery.append(f"re_retrieve:{step.step_id}")
    return {
        "require_reretrieve": True,
        "needs_repair": False,
        "unmet": unmet,
        "recovery_path": recovery,
    }


def re_retrieve(state: dict[str, Any]) -> dict[str, Any]:
    max_retries = int(state.get("max_retries", 2))
    attempts = int(state.get("retrieval_attempts", 0))
    if attempts >= (max_retries + 1):
        return {
            "reretrieve_failed": True,
            "done": True,
            "error": f"Exceeded retrieval retries: {attempts}/{max_retries}",
        }

    query = state["query"]
    top_k = int(state.get("top_k", 8))
    specialist = str(state.get("specialist") or SPECIALIST_GENERAL)
    specialist_score = float(state.get("specialist_score", 0.0))
    specialist_fallback_used = bool(state.get("specialist_fallback_used", False))
    hits, intent_payload = _retrieve_hits(query, max(top_k, 8), specialist, executable_only=True, strict_intent=False)
    active_specialist = specialist
    if (
        specialist != SPECIALIST_GENERAL
        and len(hits) < SPECIALIST_CANDIDATE_THRESHOLD
        and not specialist_fallback_used
    ):
        fallback_hits, fallback_intent = _retrieve_hits(
            query,
            max(top_k, 8),
            SPECIALIST_GENERAL,
            executable_only=True,
            strict_intent=False,
        )
        if fallback_hits:
            hits = fallback_hits
            intent_payload = fallback_intent
            specialist_fallback_used = True
            active_specialist = SPECIALIST_GENERAL
            specialist_score = 0.0

    failed_tools = {str(r.get("tool_id")) for r in state.get("execution_results", []) if r.get("status") != "success"}
    ordered_hits = sorted(hits, key=lambda h: (h.record.id in failed_tools, -h.rrf_score))
    candidates = [hit.to_dict() for hit in ordered_hits]

    if not candidates:
        return {"reretrieve_failed": True, "done": True, "error": "Re-retrieve returned no candidates."}

    return {
        "candidates": candidates,
        "intent": intent_payload,
        "retrieval_attempts": attempts + 1,
        "require_reretrieve": False,
        "reretrieve_failed": False,
        "specialist": active_specialist,
        "specialist_score": specialist_score,
        "specialist_fallback_used": specialist_fallback_used,
    }


def finalize(state: dict[str, Any]) -> dict[str, Any]:
    candidates = state.get("candidates", [])
    results = state.get("execution_results", [])
    recovery = state.get("recovery_path", [])
    unmet = state.get("unmet", [])
    adopted = []
    seen_tools = set()
    for tool_id in state.get("adopted_tools", []):
        if tool_id in seen_tools:
            continue
        seen_tools.add(tool_id)
        adopted.append(tool_id)

    failures = [r for r in results if r.get("status") != "success"]
    lines: list[str] = []
    lines.append("採用ツール:")
    lines.append(", ".join(adopted) if adopted else "(なし)")
    lines.append("")
    lines.append("失敗と回復経路:")
    if failures:
        for item in failures:
            err = item.get("error") or {}
            if isinstance(err, dict):
                code = err.get("code", "UNKNOWN")
                message = err.get("message", "")
            else:
                code = "UNKNOWN"
                message = str(err)
            lines.append(f"- {item.get('step_id')} {item.get('tool_id')} => {code}: {message}")
    else:
        lines.append("- 失敗なし")
    if recovery:
        for entry in recovery:
            lines.append(f"- recovery: {entry}")

    lines.append("")
    lines.append("未達成事項:")
    if unmet:
        for item in unmet:
            lines.append(f"- {item}")
    elif not candidates:
        lines.append("- 候補ツールを取得できませんでした。")
    else:
        lines.append("- なし")

    error = state.get("error")
    if error:
        lines.append("")
        lines.append(f"エラー: {error}")

    return {"final_answer": "\n".join(lines)}
