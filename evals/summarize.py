"""Local summaries and run-to-run diffs for eval runs (offline; no network).

Usage:
    python -m evals.summarize --run-id baseline-v0
    python -m evals.summarize --run-id v1 --diff baseline-v0

Reads evals/results/<run_id>/ records + judge caches, scores them with the same
deterministic evaluators used in LangSmith, and writes summary.json + summary.md
beside them (plus diff_<a>_to_<b>.md when --diff is given).
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from src import config

from evals.dataset import build_examples
from evals.evaluators import ALL_KEYS, evaluate

RESULTS_DIR = config.EVALS_DIR / "results"

GATE_KEYS = (
    "submission_present",
    "schema_valid",
    "status_match",
    "missing_items_match",
    "guardrail_ready_without_missing",
)

SLICE_KEYS = ("status_match", "missing_items_match", "critical_checks_match")


def _mean(values):
    return sum(values) / len(values) if values else None


def _fmt(value):
    return "-" if value is None else f"{value:.2f}"


def load_label_meta() -> dict:
    """case_id -> {expected, metadata} from the fixtures (offline)."""
    meta = {}
    for example in build_examples():
        meta[example["inputs"]["case_id"]] = {
            "expected": example["outputs"],
            "metadata": example["metadata"],
        }
    return meta


def load_run(run_id: str, root: Path = RESULTS_DIR) -> dict:
    """case_id -> {record, judge-or-None} from evals/results/<run_id>/."""
    cases_dir = root / run_id / "cases"
    judge_dir = root / run_id / "judge"
    run = {}
    for path in sorted(cases_dir.glob("case-*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        judge = None
        judge_path = judge_dir / f"{record['case_id']}.json"
        if judge_path.exists():
            judge = json.loads(judge_path.read_text(encoding="utf-8"))
        run[record["case_id"]] = {"record": record, "judge": judge}
    return run


def score_run(run_id: str, root: Path = RESULTS_DIR) -> list[dict]:
    """One row per case: deterministic scores + comments + judge verdict."""
    meta = load_label_meta()
    run = load_run(run_id, root)
    rows = []
    for case_id, item in sorted(run.items()):
        label = meta.get(case_id)
        if label is None:
            continue
        record = item["record"]
        results = evaluate(record, label["expected"], error=record.get("error"))
        scores = {result["key"]: result["score"] for result in results}
        rows.append(
            {
                "case_id": case_id,
                "category": label["metadata"]["category"],
                "difficulty": label["metadata"]["difficulty"],
                "scores": scores,
                "comments": {
                    result["key"]: result["comment"]
                    for result in results
                    if result["comment"]
                },
                "judge": item["judge"],
                "gate": all(scores[key] == 1.0 for key in GATE_KEYS),
            }
        )
    return rows


def summarize(rows: list[dict]) -> dict:
    metrics = {
        key: {
            "mean": _mean([row["scores"][key] for row in rows if key in row["scores"]]),
            "n": len([row for row in rows if key in row["scores"]]),
        }
        for key in ALL_KEYS
    }
    judged = [row for row in rows if row["judge"]]
    slices = {}
    for field in ("difficulty", "category"):
        groups = defaultdict(list)
        for row in rows:
            groups[row[field]].append(row)
        slices[field] = {
            name: {
                key: _mean([r["scores"][key] for r in members if key in r["scores"]])
                for key in SLICE_KEYS
            }
            for name, members in sorted(groups.items())
        }
    gate_passed = sum(1 for row in rows if row["gate"])
    return {
        "cases": len(rows),
        "metrics": metrics,
        "slices": slices,
        "gate": {
            "passed": gate_passed,
            "total": len(rows),
            "rate": gate_passed / len(rows) if rows else None,
            "failures": [row["case_id"] for row in rows if not row["gate"]],
        },
        "judge": {
            "n": len(judged),
            "grounded_rate": _mean([1.0 if row["judge"]["grounded"] else 0.0 for row in judged]),
            "mean_score": _mean([row["judge"]["score"] for row in judged]),
            "not_grounded": [
                row["case_id"] for row in judged if not row["judge"]["grounded"]
            ],
        },
    }


def render_summary_md(summary: dict, rows: list[dict]) -> str:
    judge = summary["judge"]
    gate = summary["gate"]
    lines = [
        f"# Eval summary - {summary['run_id']}",
        "",
        (
            f"Cases: {summary['cases']} | gate passed: {gate['passed']}/{gate['total']} | "
            f"judge grounded: {_fmt(judge['grounded_rate'])} ({judge['n']} judged, "
            f"mean score {_fmt(judge['mean_score'])})"
        ),
        "",
        "## Metrics (mean over cases)",
        "",
        "| metric | mean |",
        "|---|---|",
    ]
    for key in ALL_KEYS:
        lines.append(f"| {key} | {_fmt(summary['metrics'][key]['mean'])} |")
    lines.append(f"| judge_grounded | {_fmt(judge['grounded_rate'])} |")

    lines += [
        "",
        "## Slices by difficulty",
        "",
        "| difficulty | n | status_match | missing_items_match | critical_checks_match |",
        "|---|---|---|---|---|",
    ]
    for name, metrics in summary["slices"]["difficulty"].items():
        n = len([row for row in rows if row["difficulty"] == name])
        lines.append(
            f"| {name} | {n} | {_fmt(metrics['status_match'])} | "
            f"{_fmt(metrics['missing_items_match'])} | {_fmt(metrics['critical_checks_match'])} |"
        )

    lines += ["", "## Gate failures", ""]
    if gate["failures"]:
        for case_id in gate["failures"]:
            row = next(r for r in rows if r["case_id"] == case_id)
            failed = [key for key in GATE_KEYS if row["scores"][key] != 1.0]
            lines.append(f"- {case_id} ({row['difficulty']}): {', '.join(failed)}")
    else:
        lines.append("none")
    lines.append("")
    return "\n".join(lines)


def write_summary(run_id: str, root: Path = RESULTS_DIR) -> dict:
    rows = score_run(run_id, root)
    summary = {
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        **summarize(rows),
    }
    out_dir = root / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "summary.md").write_text(render_summary_md(summary, rows), encoding="utf-8")
    return summary


def _load_or_compute(run_id: str, root: Path) -> dict:
    path = root / run_id / "summary.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return write_summary(run_id, root)


def _rate(summary: dict, key: str):
    if key == "judge_grounded":
        return summary["judge"]["grounded_rate"]
    return summary["metrics"].get(key, {}).get("mean")


def diff_runs(a: str, b: str, root: Path = RESULTS_DIR) -> str:
    """Metric-by-metric comparison a -> b; writes and returns the markdown."""
    sa = _load_or_compute(a, root)
    sb = _load_or_compute(b, root)
    keys = (*ALL_KEYS, "judge_grounded")
    lines = [
        f"# Diff {a} -> {b}",
        "",
        f"Cases: {sa['cases']} -> {sb['cases']} | "
        f"gate passed: {sa['gate']['passed']}/{sa['gate']['total']} -> "
        f"{sb['gate']['passed']}/{sb['gate']['total']} | "
        f"judge grounded: {_fmt(sa['judge']['grounded_rate'])} -> {_fmt(sb['judge']['grounded_rate'])}",
        "",
        f"| metric | {a} | {b} | delta |",
        "|---|---|---|---|",
    ]
    for key in keys:
        va, vb = _rate(sa, key), _rate(sb, key)
        if va is None or vb is None:
            delta_text = "-"
        else:
            delta = vb - va
            delta_text = f"{'+' if delta >= 0 else ''}{delta:.2f}"
        lines.append(f"| {key} | {_fmt(va)} | {_fmt(vb)} | {delta_text} |")

    lines += [
        "",
        "## Slices by difficulty (status_match / missing_items_match / critical_checks_match)",
        "",
        f"| difficulty | {a} | {b} |",
        "|---|---|---|",
    ]
    difficulties = sorted(set(sa["slices"]["difficulty"]) | set(sb["slices"]["difficulty"]))
    for name in difficulties:
        def cell(summary):
            metrics = summary["slices"]["difficulty"].get(name)
            if not metrics:
                return "-"
            return " / ".join(_fmt(metrics[key]) for key in SLICE_KEYS)
        lines.append(f"| {name} | {cell(sa)} | {cell(sb)} |")

    if sb["gate"]["failures"]:
        lines += ["", f"Still failing the gate in {b}: {', '.join(sb['gate']['failures'])}"]
    lines.append("")
    text = "\n".join(lines)
    (root / b / f"diff_{a}_to_{b}.md").write_text(text, encoding="utf-8")
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--diff", default="", help="older run id to diff against")
    args = parser.parse_args()
    summary = write_summary(args.run_id)
    print(f"summary written for {args.run_id}: gate {summary['gate']['passed']}/{summary['gate']['total']}, judge grounded {_fmt(summary['judge']['grounded_rate'])}")
    if args.diff:
        print(diff_runs(args.diff, args.run_id))
    return 0


if __name__ == "__main__":
    sys.exit(main())
