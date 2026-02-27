"""Node implementations for the orchestration graph.

Each function takes AgentState and returns a partial state update dict.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from ai_config.retriever.hybrid_search import HybridRetriever

logger = logging.getLogger(__name__)

# Lazy-initialised globals
_retriever: HybridRetriever | None = None
_llm = None


def _get_retriever(index_dir: str | Path | None = None) -> HybridRetriever:
    """Get or create the retriever singleton."""
    global _retriever
    if _retriever is None:
        if index_dir is None:
            index_dir = Path(".index")
        _retriever = HybridRetriever(index_dir)
    return _retriever


def _get_llm():
    """Get or create the LLM singleton."""
    global _llm
    if _llm is None:
        from langchain_google_genai import ChatGoogleGenerativeAI

        _llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.1,
        )
    return _llm


# ---------- Node: retrieve ----------

def retrieve(state: dict[str, Any]) -> dict[str, Any]:
    """Search the tool registry for relevant tools."""
    query = state["query"]
    retry_count = state.get("retry_count", 0)

    retriever = _get_retriever()
    results = retriever.search(query, top_k=8)

    tools = [
        {
            "id": rec.id,
            "name": rec.name,
            "description": rec.description,
            "tool_type": rec.tool_type,
            "source_path": rec.source_path,
            "score": score,
        }
        for rec, score in results
    ]

    logger.info(
        "Retrieved %d tools for query=%r (retry=%d)",
        len(tools),
        query[:60],
        retry_count,
    )

    return {"retrieved_tools": tools, "retry_count": retry_count}


# ---------- Node: plan ----------

_PLAN_PROMPT = """\
あなたはタスクプランナーです。ユーザーリクエストと利用可能なツールを基に、実行計画を策定してください。

## ユーザーリクエスト
{query}

## 利用可能なツール
{tools_json}

## 指示
1. リクエストを達成するために必要なツールを選び、実行順序を決定してください。
2. 各ステップの入力と期待される出力を明記してください。
3. 利用可能なツールだけでは不十分な場合は、その旨を明記してください。

JSON形式で出力してください:
```json
{{
  "steps": [
    {{"tool_id": "...", "action": "...", "reason": "..."}}
  ],
  "feasibility": "full|partial|impossible",
  "notes": "..."
}}
```
"""


def plan(state: dict[str, Any]) -> dict[str, Any]:
    """Generate an execution plan using LLM."""
    query = state["query"]
    tools = state.get("retrieved_tools", [])

    if not tools:
        return {
            "plan": json.dumps({
                "steps": [],
                "feasibility": "impossible",
                "notes": "No relevant tools found in the registry.",
            }),
        }

    llm = _get_llm()
    prompt = _PLAN_PROMPT.format(
        query=query,
        tools_json=json.dumps(tools, ensure_ascii=False, indent=2),
    )

    response = llm.invoke(prompt)
    plan_text = response.content if hasattr(response, "content") else str(response)

    logger.info("Plan generated (%d chars)", len(plan_text))
    return {"plan": plan_text}


# ---------- Node: execute ----------

def execute(state: dict[str, Any]) -> dict[str, Any]:
    """Execute the plan (mock execution for Happy Path).

    In production, this would dispatch to the MCP wrapper.
    For the initial implementation, we simulate execution.
    """
    plan_text = state.get("plan", "")

    # Parse plan to extract steps
    steps = []
    try:
        # Try to extract JSON from markdown code block
        if "```json" in plan_text:
            json_str = plan_text.split("```json")[1].split("```")[0].strip()
        elif "```" in plan_text:
            json_str = plan_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = plan_text

        plan_obj = json.loads(json_str)
        steps = plan_obj.get("steps", [])
    except (json.JSONDecodeError, IndexError):
        logger.warning("Could not parse plan JSON, treating as free-text plan")

    results = []
    for step in steps:
        tool_id = step.get("tool_id", "unknown")
        action = step.get("action", "")
        results.append({
            "tool_id": tool_id,
            "action": action,
            "status": "mock_success",
            "output": f"[Mock] Executed {tool_id}: {action}",
        })

    logger.info("Executed %d steps (mock)", len(results))
    return {"execution_results": results, "error": None}


# ---------- Node: evaluate ----------

def evaluate(state: dict[str, Any]) -> dict[str, Any]:
    """Evaluate execution results and decide next action.

    Returns updated state. The routing logic is in graph.py.
    """
    error = state.get("error")
    results = state.get("execution_results", [])
    retry_count = state.get("retry_count", 0)

    if error and retry_count < 2:
        logger.info("Error detected, will retry (count=%d)", retry_count)
        return {"retry_count": retry_count + 1, "error": error}

    # Check for any failures
    failures = [r for r in results if r.get("status") not in ("mock_success", "success")]
    if failures and retry_count < 2:
        logger.info("%d failures, will retry", len(failures))
        return {
            "retry_count": retry_count + 1,
            "error": f"{len(failures)} steps failed",
        }

    return {"error": None}


# ---------- Node: respond ----------

def respond(state: dict[str, Any]) -> dict[str, Any]:
    """Generate the final response to the user."""
    query = state["query"]
    tools = state.get("retrieved_tools", [])
    plan_text = state.get("plan", "")
    results = state.get("execution_results", [])
    error = state.get("error")

    if error:
        return {
            "final_answer": f"タスクの実行中にエラーが発生しました: {error}\n\n"
            f"取得されたツール: {[t['name'] for t in tools]}",
        }

    if not tools:
        return {
            "final_answer": "リクエストに対応するツールがレジストリ内に見つかりませんでした。",
        }

    # Summarise results
    tool_names = [t["name"] for t in tools[:5]]
    step_summaries = [
        f"- {r['tool_id']}: {r['status']}" for r in results
    ]

    answer = (
        f"## 検索されたツール\n"
        f"{', '.join(tool_names)}\n\n"
        f"## 実行計画\n{plan_text[:500]}\n\n"
        f"## 実行結果\n" + "\n".join(step_summaries) if step_summaries else "(実行ステップなし)"
    )

    return {"final_answer": answer}
