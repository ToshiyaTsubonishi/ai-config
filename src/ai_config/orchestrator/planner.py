"""Planning service for planning-first orchestration."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from ai_config.contracts.approved_plan import (
    ApprovedPlan,
    FallbackStrategy,
    PlanStep,
    PlanValidationResult,
    parse_plan_text,
    ToolReference,
    render_approved_plan_summary,
)
from ai_config.orchestrator.candidate_bias import boost_hits
from ai_config.orchestrator.router import (
    SPECIALIST_CANDIDATE_THRESHOLD,
    SPECIALIST_GENERAL,
    route_specialist,
    specialist_filters,
)
from ai_config.orchestrator.validator import collect_plan_tool_ids, validate_orchestration_plan
from ai_config.registry.models import ToolRecord, load_records
from ai_config.retriever.hybrid_search import HybridRetriever
from ai_config.retriever.query_intent import infer_query_intent

logger = logging.getLogger(__name__)


class _PlannerDraftStep(BaseModel):
    step_id: str
    title: str = ""
    purpose: str = ""
    inputs: list[str] = Field(default_factory=list)
    expected_output: str = ""
    tool_id: str
    depends_on: list[str] = Field(default_factory=list)
    fallback_tool_id: str | None = None
    fallback_action: str = "replan"
    fallback_notes: str = ""
    action: str = "run"
    params: dict[str, Any] = Field(default_factory=dict)
    working_directory: str = "."


class _PlannerDraft(BaseModel):
    assumptions: list[str] = Field(default_factory=list)
    steps: list[_PlannerDraftStep] = Field(default_factory=list)
    feasibility: str = "partial"
    execution_notes: str = ""


@dataclass
class PlanningContext:
    query: str
    specialist_route: str
    specialist_score: float
    specialist_fallback_used: bool
    intent: dict[str, Any]
    candidates: list[dict[str, Any]]
    candidate_records: dict[str, ToolRecord]


@dataclass
class PlanningResult:
    plan: ApprovedPlan
    validation: PlanValidationResult
    context: PlanningContext
    resolved_records: dict[str, ToolRecord]


def _resolve_tool_kinds(intent_kinds: list[str], specialist_kinds: list[str] | None) -> list[str] | None:
    if not specialist_kinds:
        return intent_kinds or None
    if not intent_kinds:
        return specialist_kinds
    intersection = sorted(set(intent_kinds).intersection(specialist_kinds))
    return intersection or intent_kinds


def _build_invoke_summary(record: ToolRecord) -> str:
    backend = str(record.invoke.get("backend", record.tool_kind))
    command = str(record.invoke.get("command", "") or "")
    args = [str(x) for x in (record.invoke.get("args", []) or [])]
    snippet = " ".join(x for x in [command, *args[:3]] if x).strip()
    return f"{backend}: {snippet}".strip(": ").strip()


def _tool_ref_from_record(record: ToolRecord, selection_reason: str, confidence: float = 0.0) -> ToolReference:
    return ToolReference(
        tool_id=record.id,
        tool_kind=record.tool_kind,
        name=record.name,
        source_path=record.source_path,
        selection_reason=selection_reason,
        invoke_summary=_build_invoke_summary(record),
        confidence=max(0.0, min(confidence, 1.0)),
    )


def _extract_text(response: Any) -> str:
    content = response.content if hasattr(response, "content") else str(response)
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif hasattr(part, "text"):
                parts.append(str(part.text))
            else:
                parts.append(str(part))
        return "".join(parts)
    return str(content)


class OrchestrationPlanner:
    """Planning service backed by the registry index."""

    def __init__(self, index_dir: Path, repo_root: Path) -> None:
        self.index_dir = index_dir.resolve()
        self.repo_root = repo_root.resolve()
        self._retriever: HybridRetriever | None = None
        self._records_by_id: dict[str, ToolRecord] | None = None
        self._llm = None

    @property
    def retriever(self) -> HybridRetriever:
        if self._retriever is None:
            self._retriever = HybridRetriever(self.index_dir)
        return self._retriever

    @property
    def records_by_id(self) -> dict[str, ToolRecord]:
        if self._records_by_id is None:
            records = load_records(str(self.index_dir / "records.json"))
            self._records_by_id = {record.id: record for record in records}
        return self._records_by_id

    def _get_llm(self) -> Any:
        if self._llm is not None:
            return self._llm
        if not os.getenv("GOOGLE_API_KEY"):
            return None
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except Exception:
            return None
        model_name = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
        self._llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.1)
        return self._llm

    def retrieve_candidates(self, query: str, top_k: int = 8, *, strict_intent: bool = True) -> PlanningContext:
        specialist_route, specialist_score = route_specialist(query)
        specialist_fallback_used = False
        hits, intent_payload = self._retrieve_hits(
            query=query,
            top_k=top_k,
            specialist=specialist_route,
            strict_intent=strict_intent,
            executable_only=True,
        )
        active_specialist = specialist_route
        if (
            specialist_route != SPECIALIST_GENERAL
            and len(hits) < SPECIALIST_CANDIDATE_THRESHOLD
            and not specialist_fallback_used
        ):
            fallback_hits, fallback_intent = self._retrieve_hits(
                query=query,
                top_k=top_k,
                specialist=SPECIALIST_GENERAL,
                strict_intent=strict_intent,
                executable_only=True,
            )
            if fallback_hits:
                hits = fallback_hits
                intent_payload = fallback_intent
                specialist_fallback_used = True
                active_specialist = SPECIALIST_GENERAL
                specialist_score = 0.0

        candidates = [hit.to_dict() for hit in hits]
        candidate_records: dict[str, ToolRecord] = {}
        for hit in hits:
            candidate_records[hit.record.id] = hit.record

        return PlanningContext(
            query=query,
            specialist_route=active_specialist,
            specialist_score=specialist_score,
            specialist_fallback_used=specialist_fallback_used,
            intent=intent_payload,
            candidates=candidates,
            candidate_records=candidate_records,
        )

    def create_plan(
        self,
        query: str,
        *,
        top_k: int = 8,
        approval_required: bool = True,
        previous_plan: ApprovedPlan | None = None,
        replan_reason: dict[str, Any] | None = None,
    ) -> PlanningResult:
        context = self.retrieve_candidates(query, top_k=top_k)
        candidate_refs = [
            _tool_ref_from_record(
                context.candidate_records[candidate["id"]],
                selection_reason=f"Candidate retrieved for specialist route {context.specialist_route}",
                confidence=float(candidate.get("score", 0.0) or 0.0),
            )
            for candidate in context.candidates
            if candidate.get("id") in context.candidate_records
        ]

        plan = self.generate_plan_artifact(
            query=query,
            context=context,
            candidate_refs=candidate_refs,
            previous_plan=previous_plan,
            replan_reason=replan_reason,
        )
        plan.plan_id = previous_plan.plan_id if previous_plan else plan.plan_id
        plan.revision = (previous_plan.revision + 1) if previous_plan else 1
        plan.user_goal = query
        plan.specialist_route = context.specialist_route
        plan.candidate_tools = candidate_refs
        plan.approval_required = approval_required
        if replan_reason:
            plan.replan_reason = json.dumps(replan_reason, ensure_ascii=False)

        validation = self.validate_plan_artifact(plan)
        if not validation.valid:
            logger.warning("Planner output invalid, using deterministic fallback: %s", validation.errors)
            plan = self._fallback_plan(query=query, context=context, candidate_refs=candidate_refs, previous_plan=previous_plan)
            validation = self.validate_plan_artifact(plan)

        if previous_plan is not None:
            changed_tools = describe_tool_changes(previous_plan, plan)
            if changed_tools:
                change_summary = "Changed tool selections: " + "; ".join(changed_tools)
                plan.execution_notes = "\n".join([x for x in [plan.execution_notes, change_summary] if x]).strip()
                plan.notes = "\n".join([x for x in [plan.notes, change_summary] if x]).strip()

        resolved_records = self.resolve_records_for_plan(plan)
        return PlanningResult(plan=plan, validation=validation, context=context, resolved_records=resolved_records)

    def resolve_records_for_plan(self, plan: ApprovedPlan) -> dict[str, ToolRecord]:
        tool_ids = collect_plan_tool_ids(plan)
        return {tool_id: self.records_by_id[tool_id] for tool_id in tool_ids if tool_id in self.records_by_id}

    def load_plan_input(self, raw_or_path: str) -> ApprovedPlan:
        path = Path(raw_or_path)
        raw_text = path.read_text(encoding="utf-8") if path.exists() else raw_or_path
        return parse_plan_text(raw_text)

    def generate_plan_artifact(
        self,
        *,
        query: str,
        context: PlanningContext,
        candidate_refs: list[ToolReference],
        previous_plan: ApprovedPlan | None,
        replan_reason: dict[str, Any] | None,
    ) -> ApprovedPlan:
        return self._build_plan_with_llm(
            query=query,
            context=context,
            candidate_refs=candidate_refs,
            previous_plan=previous_plan,
            replan_reason=replan_reason,
        )

    def validate_plan_artifact(self, plan: ApprovedPlan) -> PlanValidationResult:
        return validate_orchestration_plan(plan, self.records_by_id)

    def controlled_replan(
        self,
        query: str,
        *,
        top_k: int = 8,
        previous_plan: ApprovedPlan,
        replan_reason: dict[str, Any],
    ) -> PlanningResult:
        return self.create_plan(
            query,
            top_k=top_k,
            approval_required=False,
            previous_plan=previous_plan,
            replan_reason=replan_reason,
        )

    def _build_plan_with_llm(
        self,
        *,
        query: str,
        context: PlanningContext,
        candidate_refs: list[ToolReference],
        previous_plan: ApprovedPlan | None,
        replan_reason: dict[str, Any] | None,
    ) -> ApprovedPlan:
        llm = self._get_llm()
        if llm is None:
            return self._fallback_plan(query=query, context=context, candidate_refs=candidate_refs, previous_plan=previous_plan)

        prompt = self._planner_prompt(
            query=query,
            context=context,
            candidate_refs=candidate_refs,
            previous_plan=previous_plan,
            replan_reason=replan_reason,
        )
        try:
            response = llm.invoke(prompt)
            content = _extract_text(response)
            draft = _PlannerDraft.model_validate(json.loads(_strip_json_fence(content)))
        except Exception as exc:
            logger.warning("LLM planning failed (%s); using deterministic fallback", exc)
            return self._fallback_plan(query=query, context=context, candidate_refs=candidate_refs, previous_plan=previous_plan)

        steps: list[PlanStep] = []
        for draft_step in draft.steps:
            record = context.candidate_records.get(draft_step.tool_id)
            if record is None:
                continue
            fallback_tool_id = draft_step.fallback_tool_id or None
            steps.append(
                PlanStep(
                    step_id=draft_step.step_id,
                    title=draft_step.title or draft_step.purpose or draft_step.step_id,
                    purpose=draft_step.purpose or draft_step.title,
                    inputs=draft_step.inputs or [query],
                    expected_output=draft_step.expected_output,
                    tool_ref=_tool_ref_from_record(
                        record,
                        selection_reason=draft_step.purpose or draft_step.title or "Selected by planner",
                        confidence=max(0.1, next((ref.confidence for ref in candidate_refs if ref.tool_id == record.id), 0.0)),
                    ),
                    depends_on=draft_step.depends_on,
                    fallback_strategy=FallbackStrategy(
                        action=str(draft_step.fallback_action or "replan"),
                        fallback_tool_id=fallback_tool_id,
                        notes=draft_step.fallback_notes,
                    ),
                    action=draft_step.action or "run",
                    params=draft_step.params,
                    working_directory=draft_step.working_directory or ".",
                )
            )

        feasibility = draft.feasibility if draft.feasibility in {"full", "partial", "impossible"} else "partial"
        return ApprovedPlan(
            user_goal=query,
            assumptions=draft.assumptions,
            specialist_route=context.specialist_route,
            candidate_tools=candidate_refs,
            steps=steps,
            approval_required=True,
            execution_notes=draft.execution_notes,
            feasibility=feasibility,
            notes=draft.execution_notes,
        )

    def _fallback_plan(
        self,
        *,
        query: str,
        context: PlanningContext,
        candidate_refs: list[ToolReference],
        previous_plan: ApprovedPlan | None,
    ) -> ApprovedPlan:
        if not candidate_refs:
            payload: dict[str, Any] = {
                "user_goal": query,
                "assumptions": ["No executable candidates were retrieved."],
                "specialist_route": context.specialist_route,
                "candidate_tools": [],
                "steps": [],
                "approval_required": True,
                "execution_notes": "Planner could not find executable candidates.",
                "feasibility": "impossible",
                "notes": "No candidates retrieved.",
                "revision": (previous_plan.revision + 1) if previous_plan else 1,
            }
            if previous_plan is not None:
                payload["plan_id"] = previous_plan.plan_id
            return ApprovedPlan.model_validate(payload)

        primary = candidate_refs[0]
        primary_record = context.candidate_records[primary.tool_id]
        params: dict[str, Any] = {}
        if primary_record.tool_kind == "toolchain_adapter":
            params = {"args": ["--help"]}

        fallback_tool_id = candidate_refs[1].tool_id if len(candidate_refs) > 1 else None
        step = PlanStep(
            step_id="step-1",
            title=f"Use {primary.name or primary.tool_id}",
            purpose=f"Execute the best registry-backed candidate for the request: {query[:120]}",
            inputs=[query],
            expected_output=f"Initial execution result from {primary.tool_id}",
            tool_ref=ToolReference.model_validate(
                primary.model_copy(
                    update={"selection_reason": f"Top-ranked candidate for user goal: {query[:120]}"}
                )
            ),
            depends_on=[],
            fallback_strategy=FallbackStrategy(
                action="use_alternative_tool" if fallback_tool_id else "replan",
                fallback_tool_id=fallback_tool_id,
                notes="Deterministic fallback planner output.",
            ),
            action="run",
            params=params,
            working_directory=".",
        )
        payload = {
            "revision": (previous_plan.revision + 1) if previous_plan else 1,
            "user_goal": query,
            "assumptions": ["Heuristic fallback planner used because the LLM was unavailable or plan validation failed."],
            "specialist_route": context.specialist_route,
            "candidate_tools": candidate_refs,
            "steps": [step],
            "approval_required": True,
            "execution_notes": "Heuristic fallback planner used.",
            "feasibility": "partial",
            "notes": "Heuristic fallback planner used.",
        }
        if previous_plan is not None:
            payload["plan_id"] = previous_plan.plan_id
        return ApprovedPlan.model_validate(payload)

    def _retrieve_hits(
        self,
        *,
        query: str,
        top_k: int,
        specialist: str,
        executable_only: bool,
        strict_intent: bool,
    ) -> tuple[list[Any], dict[str, Any]]:
        intent = infer_query_intent(query)
        filters = specialist_filters(specialist)
        tool_kinds = _resolve_tool_kinds(intent.tool_kinds, filters.get("tool_kinds")) if strict_intent else (filters.get("tool_kinds") or None)
        targets = intent.targets if strict_intent else []
        capabilities = intent.capabilities if strict_intent else []
        hits = self.retriever.search(
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

    def _planner_prompt(
        self,
        *,
        query: str,
        context: PlanningContext,
        candidate_refs: list[ToolReference],
        previous_plan: ApprovedPlan | None,
        replan_reason: dict[str, Any] | None,
    ) -> str:
        previous_plan_text = ""
        if previous_plan is not None:
            previous_plan_text = json.dumps(previous_plan.model_dump(), ensure_ascii=False, indent=2)
        replan_reason_text = json.dumps(replan_reason or {}, ensure_ascii=False, indent=2)
        candidates_text = json.dumps([candidate.model_dump() for candidate in candidate_refs], ensure_ascii=False, indent=2)
        return f"""あなたは厳格なオーケストレーションプランナーです。必ず JSON のみ返してください。

# ユーザー要求
{query}

# specialist_route
{context.specialist_route}

# 候補ツール
{candidates_text}

# 以前のプラン
{previous_plan_text or "{}"}

# 再計画理由
{replan_reason_text}

# 制約
- steps は実行順ではなく依存関係を満たす形で定義してよい
- 使用できる tool_id は候補ツールに含まれるものだけ
- step ごとに step_id/title/purpose/inputs/expected_output/tool_id/depends_on/fallback_action/fallback_tool_id/action/params/working_directory を返す
- fallback_action は retry/use_alternative_tool/replan/abort のいずれか
- 曖昧なツール名だけでなく tool_id を明示する
- 存在しない tool_id を作らない

# 返却形式
{{
  "assumptions": ["..."],
  "steps": [
    {{
      "step_id": "step-1",
      "title": "...",
      "purpose": "...",
      "inputs": ["..."],
      "expected_output": "...",
      "tool_id": "...",
      "depends_on": [],
      "fallback_action": "replan",
      "fallback_tool_id": null,
      "fallback_notes": "...",
      "action": "run",
      "params": {{}},
      "working_directory": "."
    }}
  ],
  "feasibility": "full",
  "execution_notes": "..."
}}
"""


def _strip_json_fence(text: str) -> str:
    raw = text.strip()
    if "```json" in raw:
        return raw.split("```json", 1)[1].split("```", 1)[0].strip()
    if raw.startswith("```") and raw.endswith("```"):
        return raw.split("```", 1)[1].rsplit("```", 1)[0].strip()
    return raw


def render_plan_summary(plan: ApprovedPlan) -> str:
    """Render a concise human-readable summary for CLI output."""
    return render_approved_plan_summary(plan)


def describe_tool_changes(previous_plan: ApprovedPlan, new_plan: ApprovedPlan) -> list[str]:
    """Describe tool selection changes between plan revisions."""
    previous_map = {step.step_id: step.tool_ref.tool_id for step in previous_plan.steps}
    changes: list[str] = []
    for step in new_plan.steps:
        previous_tool = previous_map.get(step.step_id)
        if previous_tool and previous_tool != step.tool_ref.tool_id:
            changes.append(f"{step.step_id}: {previous_tool} -> {step.tool_ref.tool_id}")
    return changes
