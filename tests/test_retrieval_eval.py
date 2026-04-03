from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from ai_config.evals.retrieval_eval import (
    RetrievalEvalCase,
    evaluate_retrieval_cases,
    load_retrieval_eval_cases,
    main,
    validate_expected_ids,
)
from ai_config.registry.index_builder import build_index
from ai_config.registry.models import ToolRecord
from ai_config.retriever.hybrid_search import HybridRetriever


def _build_eval_index(index_dir: Path) -> None:
    records = [
        ToolRecord(
            id="skill:frontend-patterns",
            name="frontend-patterns",
            description="Frontend development patterns for React, Next.js, state management, performance optimization, and UI best practices.",
            source_path="skills/shared/frontend-patterns/SKILL.md",
            tool_kind="skill",
            tags=["skill:frontend-patterns"],
        ),
        ToolRecord(
            id="skill:security-review",
            name="security-review",
            description="Use this skill when adding authentication, handling user input, working with secrets, creating API endpoints, or implementing payment features.",
            source_path="skills/shared/security-review/SKILL.md",
            tool_kind="skill",
            tags=["skill:security-review"],
        ),
        ToolRecord(
            id="mcp:filesystem",
            name="filesystem",
            description="Local filesystem read/write operations with directory listing support.",
            source_path="config/master/ai-sync.yaml",
            tool_kind="mcp_server",
            tags=["kind:mcp_server"],
        ),
    ]
    build_index(records, index_dir, embedding_backend="hash", vector_backend="numpy")


def test_load_retrieval_eval_cases(tmp_path: Path) -> None:
    cases_path = tmp_path / "cases.json"
    cases_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "cases": [
                    {"query": "frontend react nextjs", "expected_id": "skill:frontend-patterns"},
                    {"query": "filesystem list directory", "expected_id": "mcp:filesystem"},
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    cases = load_retrieval_eval_cases(cases_path)

    assert cases == [
        RetrievalEvalCase(query="frontend react nextjs", expected_id="skill:frontend-patterns"),
        RetrievalEvalCase(query="filesystem list directory", expected_id="mcp:filesystem"),
    ]


def test_evaluate_retrieval_cases_computes_metrics(tmp_path: Path) -> None:
    _build_eval_index(tmp_path)
    retriever = HybridRetriever(tmp_path)
    cases = [
        RetrievalEvalCase(
            query="frontend-patterns react nextjs performance",
            expected_id="skill:frontend-patterns",
        ),
        RetrievalEvalCase(
            query="filesystem list directory",
            expected_id="mcp:filesystem",
        ),
        RetrievalEvalCase(
            query="missing query",
            expected_id="skill:missing",
        ),
    ]

    report = evaluate_retrieval_cases(retriever, cases, top_k=5)

    assert report.case_count == 3
    assert report.hit_at_1 == 2 / 3
    assert report.hit_at_3 == 2 / 3
    assert report.hit_at_5 == 2 / 3
    assert round(report.mrr, 4) == round((1.0 + 1.0 + 0.0) / 3.0, 4)
    assert report.cases[0].rank == 1
    assert report.cases[1].rank == 1
    assert report.cases[2].rank is None


def test_retrieval_eval_main_writes_json_and_applies_thresholds(tmp_path: Path) -> None:
    index_dir = tmp_path / "index"
    _build_eval_index(index_dir)
    cases_path = tmp_path / "cases.json"
    output_path = tmp_path / "report.json"
    cases_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "cases": [
                    {
                        "query": "frontend-patterns react nextjs performance",
                        "expected_id": "skill:frontend-patterns",
                    },
                    {
                        "query": "filesystem list directory",
                        "expected_id": "mcp:filesystem",
                    },
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "--index-dir",
            str(index_dir),
            "--cases",
            str(cases_path),
            "--json-output",
            str(output_path),
            "--min-hit-at-3",
            "1.0",
            "--min-mrr",
            "0.7",
        ]
    )

    assert exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["metrics"]["hit_at_3"] == 1.0
    assert payload["metrics"]["mrr"] == 1.0


def test_retrieval_eval_main_fails_when_threshold_unmet(tmp_path: Path) -> None:
    index_dir = tmp_path / "index"
    _build_eval_index(index_dir)
    cases_path = tmp_path / "cases.json"
    cases_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "cases": [
                    {
                        "query": "filesystem list directory",
                        "expected_id": "skill:security-review",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "--index-dir",
            str(index_dir),
            "--cases",
            str(cases_path),
            "--min-hit-at-1",
            "1.0",
        ]
    )

    assert exit_code == 1


def test_evaluate_retrieval_cases_counts_mrr_beyond_top_5() -> None:
    hit_ids = [
        "skill:one",
        "skill:two",
        "skill:three",
        "skill:four",
        "skill:five",
        "skill:target",
    ]

    class _FakeRetriever:
        def search(self, query: str, top_k: int = 5) -> list[SimpleNamespace]:
            assert query == "deep ranking"
            assert top_k == 10
            return [SimpleNamespace(record=SimpleNamespace(id=tool_id)) for tool_id in hit_ids[:top_k]]

    report = evaluate_retrieval_cases(
        _FakeRetriever(),  # type: ignore[arg-type]
        [RetrievalEvalCase(query="deep ranking", expected_id="skill:target")],
        top_k=10,
    )

    assert report.hit_at_5 == 0.0
    assert report.mrr == 1.0 / 6.0
    assert report.cases[0].rank == 6


def test_validate_expected_ids_fails_for_missing_tool(tmp_path: Path) -> None:
    _build_eval_index(tmp_path)
    retriever = HybridRetriever(tmp_path)

    try:
        validate_expected_ids(
            retriever,
            [
                RetrievalEvalCase(
                    query="missing expected",
                    expected_id="skill:not-in-index",
                )
            ],
        )
    except ValueError as exc:
        assert "skill:not-in-index" in str(exc)
    else:
        raise AssertionError("validate_expected_ids should fail when expected_id is missing from the index")


def test_retrieval_eval_main_fails_when_top_k_below_5(tmp_path: Path) -> None:
    index_dir = tmp_path / "index"
    _build_eval_index(index_dir)
    cases_path = tmp_path / "cases.json"
    cases_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "cases": [
                    {
                        "query": "filesystem list directory",
                        "expected_id": "mcp:filesystem",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    try:
        main(
            [
                "--index-dir",
                str(index_dir),
                "--cases",
                str(cases_path),
                "--top-k",
                "3",
            ]
        )
    except ValueError as exc:
        assert "--top-k must be >= 5" in str(exc)
    else:
        raise AssertionError("main should reject top_k values below 5")


def test_retrieval_eval_main_fails_when_expected_id_missing_from_index(tmp_path: Path) -> None:
    index_dir = tmp_path / "index"
    _build_eval_index(index_dir)
    cases_path = tmp_path / "cases.json"
    cases_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "cases": [
                    {
                        "query": "filesystem list directory",
                        "expected_id": "skill:not-in-index",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    try:
        main(
            [
                "--index-dir",
                str(index_dir),
                "--cases",
                str(cases_path),
            ]
        )
    except ValueError as exc:
        assert "skill:not-in-index" in str(exc)
    else:
        raise AssertionError("main should fail fast when an expected_id is missing from the index")
