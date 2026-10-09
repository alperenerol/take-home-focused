"""Offline tests for the judge prompt and verdict model (no network calls)."""

import json

from pydantic import ValidationError

from evals import judge
from src import config


DOSSIER = {
    "case_id": "case-001",
    "status": "READY_FOR_UNDERWRITING",
    "checks": [
        {
            "check_id": "CHK-DOC-COMPLETE",
            "outcome": "PASSED",
            "rationale": "All required documents present (payslips, employer letter, ID, credit report).",
            "citations": ["POL-DOC-01", "POL-BOGUS-99"],
            "missing_items": [],
        }
    ],
    "required_actions": [],
    "summary": "Clean case.",
}


def test_build_messages_shape_and_content():
    messages = judge.build_judge_messages("case-001", DOSSIER)
    assert [m["role"] for m in messages] == ["system", "user"]
    assert messages[0]["content"] == judge.JUDGE_SYSTEM_PROMPT
    user = messages[1]["content"]
    assert "payslip" in user  # evidence from the case-service block
    assert "POL-DOC-01" in user  # cited section included
    assert "no such section" in user  # unknown id marked, not fatal
    assert json.dumps(DOSSIER["case_id"], indent=None) and '"case-001"' in user
    assert "SUBMITTED DOSSIER" in user


def test_build_messages_works_for_every_case():
    empty_dossier = {"case_id": "x", "status": "READY_FOR_UNDERWRITING", "checks": []}
    for path in sorted(config.FIXTURES_DIR.glob("case-*")):
        case_id = path.name
        dossier = dict(empty_dossier, case_id=case_id)
        messages = judge.build_judge_messages(case_id, dossier)
        assert len(messages[1]["content"]) > 500


def test_verdict_model_bounds():
    ok = judge.JudgeVerdict(
        grounded=True, score=5, unsupported_claims=[], comment="Fully grounded."
    )
    assert ok.score == 5
    try:
        judge.JudgeVerdict(grounded=False, score=9, unsupported_claims=[], comment="x")
    except ValidationError:
        pass
    else:
        raise AssertionError("score 9 should not validate")


def test_make_judge_constructs_offline():
    runnable = judge.make_judge(model="gpt-6.1-sol")
    assert hasattr(runnable, "ainvoke")
