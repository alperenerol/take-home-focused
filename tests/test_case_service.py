"""In-process tests for the case-service logic (no MCP transport involved)."""

import json

import pytest

from src.mcp_server import case_service as cs

VALID_DOSSIER = {
    "case_id": "case-001",
    "status": "READY_FOR_UNDERWRITING",
    "checks": [
        {
            "check_id": "CHK-LTV",
            "outcome": "PASSED",
            "rationale": "LTV 68.75 is band A.",
            "citations": ["POL-LTV-01"],
            "missing_items": [],
        }
    ],
    "required_actions": [],
    "summary": "Assessed; ready for underwriting.",
}


def test_get_case_files_returns_declaration_and_evidence():
    payload = json.loads(cs.get_case_files("case-001"))
    assert payload["case_id"] == "case-001"
    assert payload["declaration"]["loan"]["amount_gbp"] == 220000
    assert payload["declaration"]["assessment_date"] == "2026-10-01"
    assert payload["evidence_file_count"] == len(payload["evidence_files"]) == 6
    assert list(payload["evidence_files"]) == sorted(payload["evidence_files"])
    assert "Gross pay this period" in payload["evidence_files"]["payslip_2026-09.md"]


def test_get_case_files_rejects_bad_ids():
    with pytest.raises(ValueError, match="invalid case_id"):
        cs.get_case_files("../etc/passwd")
    with pytest.raises(ValueError, match="unknown case_id"):
        cs.get_case_files("case-999")


def test_submit_valid_dossier_stores_file(tmp_path, monkeypatch):
    monkeypatch.setattr(cs, "SUBMITTED_ROOT", tmp_path / "submitted")
    monkeypatch.setenv("WINDMILL_RUN_ID", "pytest")
    message = cs.submit_dossier("case-001", VALID_DOSSIER)
    assert "accepted" in message
    stored = json.loads((tmp_path / "submitted" / "pytest" / "case-001.json").read_text())
    assert stored["run_id"] == "pytest"
    assert stored["dossier"] == VALID_DOSSIER
    assert stored["submitted_at"]


def test_submit_rejects_invalid_dossiers(tmp_path, monkeypatch):
    monkeypatch.setattr(cs, "SUBMITTED_ROOT", tmp_path / "submitted")

    with pytest.raises(ValueError, match="dossier must be an object"):
        cs.submit_dossier("case-001", ["not", "a", "dict"])  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="missing required key"):
        cs.submit_dossier("case-001", {"case_id": "case-001"})

    bad = json.loads(json.dumps(VALID_DOSSIER))
    bad["case_id"] = "case-002"
    with pytest.raises(ValueError, match="dossier.case_id must equal"):
        cs.submit_dossier("case-001", bad)

    bad = json.loads(json.dumps(VALID_DOSSIER))
    bad["status"] = "APPROVED"
    with pytest.raises(ValueError, match="status must be one of"):
        cs.submit_dossier("case-001", bad)

    bad = json.loads(json.dumps(VALID_DOSSIER))
    bad["checks"][0]["outcome"] = "maybe"
    with pytest.raises(ValueError, match="outcome must be one of"):
        cs.submit_dossier("case-001", bad)

    bad = json.loads(json.dumps(VALID_DOSSIER))
    bad["checks"][0]["check_id"] = "CHK-NOPE"
    with pytest.raises(ValueError, match="check_id"):
        cs.submit_dossier("case-001", bad)

    bad = json.loads(json.dumps(VALID_DOSSIER))
    bad["checks"][0]["citations"] = ["the policy"]
    with pytest.raises(ValueError, match="citations"):
        cs.submit_dossier("case-001", bad)

    bad = json.loads(json.dumps(VALID_DOSSIER))
    bad["checks"] = []
    with pytest.raises(ValueError, match="non-empty list"):
        cs.submit_dossier("case-001", bad)

    bad = json.loads(json.dumps(VALID_DOSSIER))
    bad["summary"] = ""
    with pytest.raises(ValueError, match="summary"):
        cs.submit_dossier("case-001", bad)


def test_submit_is_idempotent_last_wins(tmp_path, monkeypatch):
    monkeypatch.setattr(cs, "SUBMITTED_ROOT", tmp_path / "submitted")
    monkeypatch.setenv("WINDMILL_RUN_ID", "pytest")
    cs.submit_dossier("case-001", VALID_DOSSIER)
    second = json.loads(json.dumps(VALID_DOSSIER))
    second["summary"] = "Second submission."
    cs.submit_dossier("case-001", second)
    stored = json.loads((tmp_path / "submitted" / "pytest" / "case-001.json").read_text())
    assert stored["dossier"]["summary"] == "Second submission."
