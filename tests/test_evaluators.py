"""Offline tests for the deterministic evaluators (canned records, no network)."""

from evals import evaluators


def by_key(results):
    return {r["key"]: r for r in results}


def make_dossier(
    *,
    case_id="case-001",
    status="READY_FOR_UNDERWRITING",
    checks=None,
    required_actions=None,
    summary="All checks passed.",
):
    return {
        "case_id": case_id,
        "status": status,
        "checks": checks
        if checks is not None
        else [
            {
                "check_id": "CHK-DOC-COMPLETE",
                "outcome": "PASSED",
                "rationale": "All required documents present per POL-DOC-01.",
                "citations": ["POL-DOC-01"],
                "missing_items": [],
            }
        ],
        "required_actions": required_actions if required_actions is not None else [],
        "summary": summary,
    }


EXPECTED = {
    "status": "READY_FOR_UNDERWRITING",
    "missing_items": [],
    "critical_checks": {"CHK-DOC-COMPLETE": "PASSED"},
    "key_citations": ["POL-DOC-01"],
    "required_tools": ["get_case_files", "submit_dossier"],
}


def make_actual(**overrides):
    actual = {
        "case_id": "case-001",
        "submitted": make_dossier(),
        "structured": make_dossier(),
        "tool_names": ["get_case_files", "search_policy", "submit_dossier"],
    }
    actual.update(overrides)
    return actual


def test_keys_are_stable():
    results = evaluators.evaluate(make_actual(), EXPECTED)
    assert tuple(r["key"] for r in results) == evaluators.ALL_KEYS


def test_perfect_record_scores_all_ones():
    results = by_key(evaluators.evaluate(make_actual(), EXPECTED))
    assert all(r["score"] == 1.0 for r in results.values()), results


def test_no_submission_zeros_everything_with_reason():
    results = by_key(evaluators.evaluate(make_actual(submitted=None), EXPECTED))
    assert results["submission_present"]["score"] == 0.0
    assert "no dossier" in results["submission_present"]["comment"]
    for key in evaluators.ALL_KEYS[1:]:
        assert results[key]["score"] == 0.0
        assert "no submission" in results[key]["comment"]


def test_run_error_zeros_all_with_error_text():
    results = by_key(evaluators.evaluate(None, EXPECTED, error="provider 500"))
    assert all(r["score"] == 0.0 for r in results.values())
    assert "provider 500" in results["status_match"]["comment"]


def test_status_mismatch():
    dossier = make_dossier(status="EXPERT_MANUAL_REVIEW_REQUIRED")
    results = by_key(evaluators.evaluate(make_actual(submitted=dossier), EXPECTED))
    assert results["status_match"]["score"] == 0.0
    assert "expected READY_FOR_UNDERWRITING" in results["status_match"]["comment"]
    assert results["guardrail_ready_without_missing"]["score"] == 1.0


def test_missing_items_delta_comment():
    dossier = make_dossier()
    dossier["checks"][0]["missing_items"] = ["employer_letter"]
    expected = dict(EXPECTED, missing_items=["payslip_month_1"])
    results = by_key(evaluators.evaluate(make_actual(submitted=dossier), expected))
    assert results["missing_items_match"]["score"] == 0.0
    comment = results["missing_items_match"]["comment"]
    assert "employer_letter" in comment and "payslip_month_1" in comment


def test_critical_checks_partial_fraction():
    checks = [
        {"check_id": f"CHK-{name}", "outcome": "PASSED", "rationale": "r", "citations": ["POL-GEN-01"], "missing_items": []}
        for name in ("DOC-COMPLETE", "LTV", "CREDIT", "AFFORDABILITY")
    ]
    checks[-1]["outcome"] = "EXCEPTION_FLAGGED"
    expected = dict(
        EXPECTED,
        critical_checks={"CHK-DOC-COMPLETE": "PASSED", "CHK-LTV": "PASSED", "CHK-CREDIT": "PASSED", "CHK-AFFORDABILITY": "PASSED"},
    )
    results = by_key(evaluators.evaluate(make_actual(submitted=make_dossier(checks=checks)), expected))
    assert results["critical_checks_match"]["score"] == 0.75
    assert "CHK-AFFORDABILITY" in results["critical_checks_match"]["comment"]


def test_required_tools_fraction():
    expected = dict(EXPECTED, required_tools=["get_case_files", "search_policy", "mortgage_calculator"])
    results = by_key(evaluators.evaluate(make_actual(), expected))
    assert abs(results["required_tools_used"]["score"] - 2 / 3) < 1e-9
    assert "mortgage_calculator" in results["required_tools_used"]["comment"]


def test_invalid_citation_scores_zero():
    dossier = make_dossier()
    dossier["checks"][0]["citations"] = ["POL-BOGUS-01"]
    results = by_key(evaluators.evaluate(make_actual(submitted=dossier), EXPECTED))
    assert results["citations_valid"]["score"] == 0.0
    assert "POL-BOGUS-01" in results["citations_valid"]["comment"]
    assert results["key_citations_present"]["score"] == 0.0


def test_no_citations_at_all_scores_zero():
    dossier = make_dossier()
    dossier["checks"][0]["citations"] = []
    results = by_key(evaluators.evaluate(make_actual(submitted=dossier), EXPECTED))
    assert results["citations_valid"]["score"] == 0.0


def test_schema_invalid_dossier():
    dossier = make_dossier()
    dossier["checks"][0]["outcome"] = "MAYBE"
    results = by_key(evaluators.evaluate(make_actual(submitted=dossier), EXPECTED))
    assert results["schema_valid"]["score"] == 0.0


def test_guardrail_ready_with_missing_is_violation():
    dossier = make_dossier()
    dossier["checks"][0]["missing_items"] = ["payslip_month_1"]
    expected = dict(EXPECTED, missing_items=["payslip_month_1"])
    results = by_key(evaluators.evaluate(make_actual(submitted=dossier), expected))
    assert results["guardrail_ready_without_missing"]["score"] == 0.0
    assert results["missing_items_match"]["score"] == 1.0


def test_section_ids_load():
    ids = evaluators._section_ids()
    assert len(ids) == 12
    assert "POL-STAT-01" in ids
