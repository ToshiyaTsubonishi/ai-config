"""Golden-set retrieval evaluation for selector search quality."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ai_config.retriever.hybrid_search import HybridRetriever


@dataclass(frozen=True)
class RetrievalEvalCase:
    query: str
    expected_id: str


@dataclass(frozen=True)
class RetrievalEvalCaseResult:
    query: str
    expected_id: str
    rank: int | None
    top_ids: list[str]


@dataclass(frozen=True)
class RetrievalEvalReport:
    case_count: int
    top_k: int
    hit_at_1: float
    hit_at_3: float
    hit_at_5: float
    mrr: float
    cases: list[RetrievalEvalCaseResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_count": self.case_count,
            "top_k": self.top_k,
            "metrics": {
                "hit_at_1": self.hit_at_1,
                "hit_at_3": self.hit_at_3,
                "hit_at_5": self.hit_at_5,
                "mrr": self.mrr,
            },
            "cases": [asdict(case) for case in self.cases],
        }


def load_retrieval_eval_cases(path: Path) -> list[RetrievalEvalCase]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Eval file must contain a JSON object: {path}")

    raw_cases = payload.get("cases", [])
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError(f"Eval file must contain a non-empty 'cases' array: {path}")

    cases: list[RetrievalEvalCase] = []
    for entry in raw_cases:
        if not isinstance(entry, dict):
            raise ValueError(f"Eval case must be a JSON object: {entry!r}")
        query = str(entry.get("query") or "").strip()
        expected_id = str(entry.get("expected_id") or "").strip()
        if not query or not expected_id:
            raise ValueError(f"Eval case requires non-empty query and expected_id: {entry!r}")
        cases.append(RetrievalEvalCase(query=query, expected_id=expected_id))
    return cases


def evaluate_retrieval_cases(
    retriever: HybridRetriever,
    cases: list[RetrievalEvalCase],
    *,
    top_k: int = 5,
) -> RetrievalEvalReport:
    results: list[RetrievalEvalCaseResult] = []
    hit_at_1 = 0
    hit_at_3 = 0
    hit_at_5 = 0
    reciprocal_rank_sum = 0.0

    for case in cases:
        hits = retriever.search(case.query, top_k=top_k)
        top_ids = [hit.record.id for hit in hits]
        rank = top_ids.index(case.expected_id) + 1 if case.expected_id in top_ids else None

        if rank == 1:
            hit_at_1 += 1
        if rank is not None and rank <= 3:
            hit_at_3 += 1
        if rank is not None and rank <= 5:
            hit_at_5 += 1
            reciprocal_rank_sum += 1.0 / rank

        results.append(
            RetrievalEvalCaseResult(
                query=case.query,
                expected_id=case.expected_id,
                rank=rank,
                top_ids=top_ids,
            )
        )

    total = len(cases)
    return RetrievalEvalReport(
        case_count=total,
        top_k=top_k,
        hit_at_1=hit_at_1 / total,
        hit_at_3=hit_at_3 / total,
        hit_at_5=hit_at_5 / total,
        mrr=reciprocal_rank_sum / total,
        cases=results,
    )


def _threshold_failures(
    report: RetrievalEvalReport,
    *,
    min_hit_at_1: float | None,
    min_hit_at_3: float | None,
    min_hit_at_5: float | None,
    min_mrr: float | None,
) -> list[str]:
    failures: list[str] = []
    thresholds = [
        ("hit_at_1", report.hit_at_1, min_hit_at_1),
        ("hit_at_3", report.hit_at_3, min_hit_at_3),
        ("hit_at_5", report.hit_at_5, min_hit_at_5),
        ("mrr", report.mrr, min_mrr),
    ]
    for name, actual, minimum in thresholds:
        if minimum is not None and actual < minimum:
            failures.append(f"{name}={actual:.4f} fell below threshold {minimum:.4f}")
    return failures


def _print_human_report(report: RetrievalEvalReport) -> None:
    print("Retrieval Eval")
    print(f"Cases: {report.case_count}")
    print(
        "Metrics: "
        f"hit@1={report.hit_at_1:.4f} "
        f"hit@3={report.hit_at_3:.4f} "
        f"hit@5={report.hit_at_5:.4f} "
        f"mrr={report.mrr:.4f}"
    )
    print("")
    for case in report.cases:
        rank = "-" if case.rank is None else str(case.rank)
        print(f"[rank={rank}] {case.query}")
        print(f"  expected: {case.expected_id}")
        print(f"  top_ids: {', '.join(case.top_ids)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run golden-set retrieval evaluation for selector search.")
    parser.add_argument("--index-dir", type=Path, default=Path(".index"), help="Index directory")
    parser.add_argument(
        "--cases",
        type=Path,
        default=Path("config/evals/retrieval_golden_cases.json"),
        help="Path to retrieval eval JSON cases",
    )
    parser.add_argument("--top-k", type=int, default=5, help="Search top-k for evaluation")
    parser.add_argument("--json-output", type=Path, default=None, help="Optional path to write JSON report")
    parser.add_argument("--min-hit-at-1", type=float, default=None, help="Fail if hit@1 is below this value")
    parser.add_argument("--min-hit-at-3", type=float, default=None, help="Fail if hit@3 is below this value")
    parser.add_argument("--min-hit-at-5", type=float, default=None, help="Fail if hit@5 is below this value")
    parser.add_argument("--min-mrr", type=float, default=None, help="Fail if MRR is below this value")
    args = parser.parse_args(argv)

    retriever = HybridRetriever(args.index_dir)
    cases = load_retrieval_eval_cases(args.cases)
    report = evaluate_retrieval_cases(retriever, cases, top_k=max(args.top_k, 5))

    _print_human_report(report)

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    failures = _threshold_failures(
        report,
        min_hit_at_1=args.min_hit_at_1,
        min_hit_at_3=args.min_hit_at_3,
        min_hit_at_5=args.min_hit_at_5,
        min_mrr=args.min_mrr,
    )
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
