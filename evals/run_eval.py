"""Eval runner: assess a dataset split and score it through LangSmith experiments.

Usage:
    python -m evals.run_eval --run-id baseline-v0
    python -m evals.run_eval --run-id v1 --cases case-001,case-002
    python -m evals.run_eval --run-id baseline-v0 --no-judge --concurrency 2

For every example the target runs the assessment agent end to end (same code path as
the CLI), reads the dossier the agent submitted through the case-service (under
submitted/<run_id>/), saves a local record under evals/results/<run_id>/cases/ and
returns it as the run output. LangSmith then scores each run with:
    - the nine deterministic evaluators (evals/evaluators.py)
    - the groundedness judge (evals/judge.py); verdicts are also cached under
      evals/results/<run_id>/judge/ so summaries stay reproducible offline

The target builds one agent per process (sharing the MCP case-service session) and
sets WINDMILL_RUN_ID before the build, so the case-service stores this run's
submissions under submitted/<run_id>/.
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from src import config
from src.agent import build_agent

from evals.evaluators import deterministic_evaluators
from evals.judge import judge_case

RESULTS_DIR = config.EVALS_DIR / "results"

USER_MESSAGE = "Assess mortgage case {case_id} end to end and submit the dossier through the case-service."


def results_dir(run_id: str) -> Path:
    return RESULTS_DIR / run_id


def submission_path(run_id: str, case_id: str) -> Path:
    return config.SUBMITTED_DIR / run_id / f"{case_id}.json"


def record_path(run_id: str, case_id: str) -> Path:
    return results_dir(run_id) / "cases" / f"{case_id}.json"


def extract_tool_names(messages) -> list[str]:
    """Tool-call names in order of appearance across an agent message list."""
    names = []
    for message in messages:
        for call in getattr(message, "tool_calls", None) or []:
            if isinstance(call, dict):
                name = call.get("name")
            else:
                name = getattr(call, "name", None)
            if name:
                names.append(name)
    return names


def _write_record(run_id: str, record: dict) -> None:
    path = record_path(run_id, record["case_id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def make_target(run_id: str):
    """Async LangSmith target: one assessment per case; persists a local record."""
    holder: dict = {"agent": None}
    lock = asyncio.Lock()

    async def target(inputs: dict) -> dict:
        case_id = inputs["case_id"]
        async with lock:
            if holder["agent"] is None:
                holder["agent"] = await build_agent()
        try:
            result = await holder["agent"].ainvoke(
                {"messages": [{"role": "user", "content": USER_MESSAGE.format(case_id=case_id)}]}
            )
        except Exception as exc:  # record, then let langsmith mark the run failed
            _write_record(
                run_id,
                {
                    "case_id": case_id,
                    "error": f"{type(exc).__name__}: {exc}",
                    "submitted": None,
                    "structured": None,
                    "tool_names": [],
                    "model": config.AGENT_MODEL,
                    "assessed_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            raise
        structured = result.get("structured_response")
        dump = getattr(structured, "model_dump", None)
        if callable(dump):
            structured = dump()
        submitted = None
        path = submission_path(run_id, case_id)
        if path.exists():
            submitted = json.loads(path.read_text(encoding="utf-8"))["dossier"]
        record = {
            "case_id": case_id,
            "submitted": submitted,
            "structured": structured,
            "tool_names": extract_tool_names(result.get("messages", [])),
            "model": config.AGENT_MODEL,
            "assessed_at": datetime.now(timezone.utc).isoformat(),
        }
        _write_record(run_id, record)
        return record

    return target


def make_judge_evaluator(run_id: str):
    """LangSmith evaluator wrapping the groundedness judge; caches each verdict."""

    async def judge_evaluator(run, example) -> dict:
        actual = run.outputs if isinstance(run.outputs, dict) else None
        dossier = (actual or {}).get("submitted")
        case_id = (getattr(run, "inputs", None) or {}).get("case_id") or (
            getattr(example, "inputs", None) or {}
        ).get("case_id")
        if not dossier or not case_id:
            return {"key": "judge_grounded", "score": 0.0, "comment": "no submission to judge"}
        try:
            verdict = await judge_case(case_id, dossier)
        except Exception as exc:
            return {"key": "judge_grounded", "score": 0.0, "comment": f"judge failed: {exc}"}
        cache = results_dir(run_id) / "judge" / f"{case_id}.json"
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(verdict.model_dump_json(indent=2) + "\n", encoding="utf-8")
        comment = f"score {verdict.score}/5 - {verdict.comment}"
        if verdict.unsupported_claims:
            comment += f" | unsupported: {verdict.unsupported_claims}"
        return {
            "key": "judge_grounded",
            "score": 1.0 if verdict.grounded else 0.0,
            "comment": comment,
        }

    return judge_evaluator


async def _run(args) -> int:
    from langsmith import Client

    from evals.dataset import DATASET_NAME

    os.environ["WINDMILL_RUN_ID"] = args.run_id  # set before the agent (and MCP server) is built

    client = Client()
    examples = list(client.list_examples(dataset_name=DATASET_NAME))
    if args.cases:
        wanted = {c.strip() for c in args.cases.split(",") if c.strip()}
        examples = [e for e in examples if (e.inputs or {}).get("case_id") in wanted]
        found = {(e.inputs or {}).get("case_id") for e in examples}
        unknown = wanted - found
        if unknown:
            print(f"warning: case ids not in the dataset: {sorted(unknown)}")
    if not examples:
        print("no examples selected; nothing to run")
        return 1

    evaluators: list = [deterministic_evaluators]
    if not args.no_judge:
        evaluators.append(make_judge_evaluator(args.run_id))

    print(f"running {len(examples)} case(s) under run id {args.run_id!r} ...")
    experiment = await client.aevaluate(
        make_target(args.run_id),
        data=examples,
        evaluators=evaluators,
        experiment_prefix=args.run_id,
        max_concurrency=args.concurrency,
        metadata={"protocol": "pre-assessment-evals", "run_id": args.run_id},
        description=f"Windmill Bank pre-assessment eval run {args.run_id}",
    )
    print(f"experiment: {experiment.experiment_name}")
    url = getattr(experiment, "url", None)
    if url:
        print(f"experiment url: {url}")
    print(f"local records: {results_dir(args.run_id)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True, help="eval run id, e.g. baseline-v0")
    parser.add_argument("--cases", default="", help="comma-separated case ids (default: all)")
    parser.add_argument("--no-judge", action="store_true", help="skip the groundedness judge")
    parser.add_argument("--concurrency", type=int, default=2)
    args = parser.parse_args()
    return asyncio.run(_run(args))


if __name__ == "__main__":
    sys.exit(main())
