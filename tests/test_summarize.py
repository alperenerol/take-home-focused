"""Offline tests for summaries and diffs (synthetic rows and fake results trees)."""

import json

from evals import summarize


def make_row(case_id, difficulty, overrides=None, judge=None, category="employed"):
    scores = {key: 1.0 for key in summarize.ALL_KEYS}
    scores.update(overrides or {})
    return {
        "case_id": case_id,
        "category": category,
        "difficulty": difficulty,
        "scores": scores,
        "comments": {},
        "judge": judge,
        "gate": all(scores[key] == 1.0 for key in summarize.GATE_KEYS),
    }


def test_summarize_metrics_slices_gate():
    rows = [
        make_row("case-001", "clean"),
        make_row("case-002", "boundary", {"status_match": 0.0}),
        make_row(
            "case-003",
            "failure",
            {"guardrail_ready_without_missing": 0.0},
            judge={"grounded": False, "score": 2, "comment": "hmm"},
        ),
    ]
    summary = summarize.summarize(rows)
    assert summary["cases"] == 3
    assert abs(summary["metrics"]["status_match"]["mean"] - 2 / 3) < 1e-9
    assert summary["gate"]["passed"] == 1
    assert summary["gate"]["failures"] == ["case-002", "case-003"]
    assert summary["judge"]["grounded_rate"] == 0.0
    assert summary["judge"]["not_grounded"] == ["case-003"]
    assert summary["slices"]["difficulty"]["clean"]["status_match"] == 1.0


def test_write_summary_with_error_records(tmp_path):
    root = tmp_path / "results"
    run = root / "demo"
    (run / "cases").mkdir(parents=True)
    (run / "judge").mkdir()
    (run / "cases" / "case-001.json").write_text(
        json.dumps({"case_id": "case-001", "error": "boom", "submitted": None, "tool_names": []}),
        encoding="utf-8",
    )
    (run / "cases" / "case-002.json").write_text(
        json.dumps({"case_id": "case-002", "submitted": {}, "tool_names": []}),
        encoding="utf-8",
    )
    (run / "judge" / "case-002.json").write_text(
        json.dumps({"grounded": True, "score": 4, "unsupported_claims": [], "comment": "ok"}),
        encoding="utf-8",
    )

    summary = summarize.write_summary("demo", root)
    assert summary["cases"] == 2
    assert summary["gate"]["passed"] == 0
    assert summary["gate"]["failures"] == ["case-001", "case-002"]
    assert summary["judge"]["n"] == 1

    md = (run / "summary.md").read_text(encoding="utf-8")
    assert md.startswith("# Eval summary - demo")
    assert "## Gate failures" in md and "case-001" in md
    assert (run / "summary.json").exists()


def test_diff_runs(tmp_path):
    root = tmp_path / "results"
    base_metrics = {key: {"mean": 1.0, "n": 2} for key in summarize.ALL_KEYS}

    def write_summary(run_id, status_mean, gate_passed, failures, grounded):
        (root / run_id).mkdir(parents=True)
        metrics = dict(base_metrics)
        metrics["status_match"] = {"mean": status_mean, "n": 2}
        payload = {
            "run_id": run_id,
            "cases": 2,
            "metrics": metrics,
            "slices": {"difficulty": {"clean": {"status_match": status_mean, "missing_items_match": 1.0, "critical_checks_match": 1.0}}},
            "gate": {"passed": gate_passed, "total": 2, "rate": gate_passed / 2, "failures": failures},
            "judge": {"n": 2, "grounded_rate": grounded, "mean_score": 4.0, "not_grounded": []},
        }
        (root / run_id / "summary.json").write_text(json.dumps(payload), encoding="utf-8")

    write_summary("base", 0.5, 1, ["case-002"], 0.5)
    write_summary("fixed", 1.0, 2, [], 1.0)

    text = summarize.diff_runs("base", "fixed", root)
    assert "gate passed: 1/2 -> 2/2" in text
    assert "| status_match | 0.50 | 1.00 | +0.50 |" in text
    assert "| judge_grounded | 0.50 | 1.00 | +0.50 |" in text
    assert (root / "fixed" / "diff_base_to_fixed.md").read_text(encoding="utf-8") == text
