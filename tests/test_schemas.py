"""Schema tests: vocabulary sync with the case-service, dossier validation, JSON schema."""

import pytest
from pydantic import ValidationError

from src.mcp_server import case_service as cs
from src.schemas import CheckId, CheckOutcome, Dossier, DossierStatus

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


def test_vocabularies_match_case_service():
    assert {s.value for s in DossierStatus} == set(cs.STATUSES)
    assert {o.value for o in CheckOutcome} == set(cs.OUTCOMES)
    assert {c.value for c in CheckId} == set(cs.CHECK_IDS)


def test_valid_dossier_validates():
    dossier = Dossier.model_validate(VALID_DOSSIER)
    assert dossier.status is DossierStatus.READY
    assert dossier.checks[0].outcome is CheckOutcome.PASSED
    assert dossier.checks[0].check_id is CheckId.LTV


def test_invalid_enum_rejected():
    with pytest.raises(ValidationError):
        Dossier.model_validate({**VALID_DOSSIER, "status": "APPROVED"})
    with pytest.raises(ValidationError):
        bad = {**VALID_DOSSIER, "checks": [{**VALID_DOSSIER["checks"][0], "outcome": "MAYBE"}]}
        Dossier.model_validate(bad)


def test_missing_key_rejected():
    payload = {k: v for k, v in VALID_DOSSIER.items() if k != "summary"}
    with pytest.raises(ValidationError):
        Dossier.model_validate(payload)


def test_json_schema_contains_enums_and_serialises():
    schema = Dossier.model_json_schema()
    blob = str(schema)
    for member in ("READY_FOR_UNDERWRITING", "ACTION_REQUIRED", "CHK-AFFORDABILITY"):
        assert member in blob
    assert schema["properties"]["status"]  # present as a structured field
