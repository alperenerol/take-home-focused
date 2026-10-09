"""Collect per-case trace links and stats from a finished experiment (post-hoc).

Usage:
    python -m evals.links --run-id baseline-v0 --experiment baseline-v0-abc12345

Writes evals/results/<run_id>/links.json: per case - root run id, trace id, UI URL,
root latency, llm/tool/chain call counts, token sums and error counts. The case
mapping comes from each root run's reference example (dataset inputs carry the case
id). With no --experiment the newest project whose name starts with '<run_id>-' wins.
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from src import config

from evals.summarize import RESULTS_DIR

SELECTS = [
    "ID",
    "NAME",
    "RUN_TYPE",
    "STATUS",
    "START_TIME",
    "END_TIME",
    "LATENCY_SECONDS",
    "ERROR",
    "TRACE_ID",
    "REFERENCE_EXAMPLE_ID",
    "TOTAL_TOKENS",
    "PROMPT_TOKENS",
    "COMPLETION_TOKENS",
    "TOTAL_COST",
    "IS_ROOT",
]


def trace_url(org_id: str, project_id: str, trace_id: str) -> str:
    return f"https://smith.langchain.com/o/{org_id}/projects/p/{project_id}/r/{trace_id}"


def trace_stats(kids) -> dict:
    """Aggregate one trace's runs into review stats. Pure."""
    llms = [k for k in kids if k.run_type == "llm"]

    def token_sum(field):
        return sum((getattr(k, field, None) or 0) for k in llms)

    return {
        "llm_calls": len(llms),
        "tool_calls": sum(1 for k in kids if k.run_type == "tool"),
        "chain_calls": sum(1 for k in kids if k.run_type == "chain"),
        "errors": sum(
            1
            for k in kids
            if getattr(k, "status", None) == "error" or getattr(k, "error", None)
        ),
        "total_tokens": token_sum("total_tokens"),
        "prompt_tokens": token_sum("prompt_tokens"),
        "completion_tokens": token_sum("completion_tokens"),
    }


async def collect(
    run_id: str, experiment: str | None = None, *, client=None
) -> dict:
    from langsmith import Client

    client = client or Client()
    projects = list(client.list_projects())
    if experiment:
        proj = next((p for p in projects if p.name == experiment), None)
        if proj is None:
            raise SystemExit(f"experiment {experiment!r} not found")
    else:
        candidates = [p for p in projects if (p.name or "").startswith(f"{run_id}-")]
        if not candidates:
            raise SystemExit(f"no experiment found with prefix {run_id + '-'!r}")
        proj = max(candidates, key=lambda p: p.start_time or datetime.min)
    project_id = str(proj.id)
    org_id = str(getattr(proj, "tenant_id", "") or "")

    roots = [
        r
        async for r in client.runs.query(
            project_ids=[project_id], is_root=True, selects=SELECTS, page_size=100  # type: ignore[arg-type]
        )
    ]
    cases = {}
    for root in roots:
        case_id = None
        if root.reference_example_id:
            example = client.read_example(str(root.reference_example_id))
            case_id = (example.inputs or {}).get("case_id")
        if not case_id:
            continue
        trace_id = str(root.trace_id or root.id)
        kids = [
            r
            async for r in client.runs.query(
                project_ids=[project_id],
                trace_id=trace_id,
                selects=SELECTS,  # type: ignore[arg-type]
                page_size=100,
            )
        ]
        stats = trace_stats(kids)
        cases[case_id] = {
            "run_id": str(root.id),
            "trace_id": trace_id,
            "url": trace_url(org_id, project_id, trace_id),
            "latency_seconds": root.latency_seconds,
            **stats,
        }

    return {
        "run_id": run_id,
        "experiment": proj.name,
        "project_id": project_id,
        "org_id": org_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--experiment", default=None)
    args = parser.parse_args()

    payload = asyncio.run(collect(args.run_id, args.experiment))
    out_dir = RESULTS_DIR / args.run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "links.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    cases = payload["cases"]
    total_tokens = sum(c["total_tokens"] for c in cases.values())
    latencies = [c["latency_seconds"] for c in cases.values() if c["latency_seconds"]]
    print(f"links written: {path}")
    print(f"cases: {len(cases)} | total tokens: {total_tokens:,}")
    if latencies:
        print(f"latency: mean {sum(latencies) / len(latencies):.1f}s, max {max(latencies):.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
