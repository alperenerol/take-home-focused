"""Offline tests for the judge calibration export/compare flow."""

import json
import re

from evals import calibration
from evals.summarize import load_label_meta, RESULTS_DIR


def build_fake_run(tmp_path, case_ids):
    root = tmp_path / "results"
    run = root / "demo"
    (run / "cases").mkdir(parents=True)
    (run / "judge").mkdir()
    verdicts = {}
    for index, case_id in enumerate(case_ids):
        (run / "cases" / f"{case_id}.json").write_text(
            json.dumps(
                {
                    "case_id": case_id,
                    "submitted": {
                        "status": "READY_FOR_UNDERWRITING",
                        "checks": [
                            {
                                "check_id": "CHK-DOC-COMPLETE",
                                "outcome": "PASSED",
                                "rationale": "all present per POL-DOC-01",
                                "citations": ["POL-DOC-01"],
                                "missing_items": [],
                            }
                        ],
                        "required_actions": [],
                        "summary": "clean",
                    },
                    "tool_names": ["get_case_files", "submit_dossier"],
                }
            ),
            encoding="utf-8",
        )
        grounded = index % 2 == 0
        verdict = {
            "grounded": grounded,
            "score": 5 if grounded else 2,
            "unsupported_claims": [],
            "comment": "looks fine",
        }
        (run / "judge" / f"{case_id}.json").write_text(json.dumps(verdict), encoding="utf-8")
        verdicts[case_id] = verdict
    return root, verdicts


def test_export_pick_and_compare(tmp_path):
    meta = load_label_meta()
    by_difficulty = {}
    for case_id in sorted(meta):
        by_difficulty.setdefault(meta[case_id]["metadata"]["difficulty"], case_id)
    chosen = [by_difficulty["clean"], by_difficulty["boundary"], by_difficulty["failure"]]

    root, verdicts = build_fake_run(tmp_path, chosen)
    sheet = calibration.export("demo", n=3, root=root)
    text = sheet.read_text(encoding="utf-8")
    assert "## Item 1" in text
    assert "## Judge reference (do not read before labelling)" in text
    items = json.loads((root / "demo" / "calibration_items.json").read_text(encoding="utf-8"))
    assert set(items) == set(chosen)

    # unfilled template must NOT be parsed as a call
    assert calibration.CALL_RE.findall(text) == []

    try:
        calibration.export("demo", n=3, root=root)
    except SystemExit:
        pass
    else:
        raise AssertionError("expected a refusal to overwrite the sheet")

    # fill: two agreements, one deliberate disagreement
    calls = []
    for index, case_id in enumerate(items):
        judge = verdicts[case_id]
        if index < 2:
            calls.append(("yes" if judge["grounded"] else "no", judge["score"]))
        else:
            calls.append(("no" if judge["grounded"] else "yes", 1))
    filler = iter(f"{grounded}, score {score}, note" for grounded, score in calls)
    filled = re.sub(
        re.escape(calibration.CALL_BLANK), lambda m: "**Your call:** " + next(filler), text
    )
    sheet.write_text(filled, encoding="utf-8")

    result = calibration.compare("demo", root=root)
    assert result["labelled"] == 3
    assert abs(result["agreement"] - 2 / 3) < 1e-9
    assert result["mean_abs_score_delta"] >= 0
    assert (root / "demo" / "calibration_results.json").exists()


def test_compare_without_sheet_exits(tmp_path):
    root = tmp_path / "results"
    (root / "demo").mkdir(parents=True)
    try:
        calibration.compare("demo", root=root)
    except SystemExit:
        pass
    else:
        raise AssertionError("expected SystemExit when no sheet exists")


def test_results_dir_default_is_repo_evals_results():
    assert RESULTS_DIR.name == "results" and RESULTS_DIR.parent.name == "evals"
