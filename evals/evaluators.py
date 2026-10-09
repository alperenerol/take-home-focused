"""Deterministic evaluators for the pre-assessment protocol.

Code-only scoring over the submitted dossier and the run's tool trajectory. The one
model-based signal in the protocol is the groundedness judge (evals/judge.py); these
evaluators are exact and reproducible.

The eval runner's target returns an "actual" record:
    {"case_id": ..., "submitted": dict | None, "structured": dict | None,
     "tool_names": [...]}

`evaluate()` is the pure core (offline-testable). `deterministic_evaluators()` adapts
it to the LangSmith evaluator signature (run, example) and returns all results at once.
"""

from pydantic import ValidationError

from src.schemas import Dossier
from src.tools.search_policy import load_policy_sections

ALL_KEYS = (
    "submission_present",
    "schema_valid",
    "status_match",
    "missing_items_match",
    "critical_checks_match",
    "required_tools_used",
    "citations_valid",
    "key_citations_present",
    "guardrail_ready_without_missing",
)


def _r(key: str, score: float, comment: str = "") -> dict:
    return {"key": key, "score": float(score), "comment": comment}


def _section_ids() -> set[str]:
    return {doc.metadata["section_id"] for doc in load_policy_sections()}


def _dossier_citations(dossier: dict) -> list[str]:
    citations: list[str] = []
    for check in dossier.get("checks", []):
        citations.extend(check.get("citations") or [])
    return citations


def _all_missing_items(dossier: dict) -> list[str]:
    items: list[str] = []
    for check in dossier.get("checks", []):
        items.extend(check.get("missing_items") or [])
    return items


def evaluate(actual: dict | None, expected: dict, *, error: str | None = None) -> list[dict]:
    """All deterministic results for one (actual, expected) pair. Pure; JSON in/out."""
    expected = expected or {}

    if error or not actual:
        reason = f"run error: {error}" if error else "no run output recorded"
        return [_r(key, 0, reason) for key in ALL_KEYS]

    submitted = actual.get("submitted")
    tool_names = actual.get("tool_names") or []
    results = []

    if not submitted:
        results.append(
            _r("submission_present", 0, "no dossier was submitted through the case-service")
        )
        results.extend(_r(key, 0, "no submission to score") for key in ALL_KEYS[1:])
        return results
    results.append(_r("submission_present", 1))

    try:
        Dossier.model_validate(submitted)
        results.append(_r("schema_valid", 1))
    except ValidationError as exc:
        results.append(_r("schema_valid", 0, f"dossier violates the schema: {str(exc)[:300]}"))

    got_status = submitted.get("status")
    want_status = expected.get("status")
    results.append(
        _r("status_match", got_status == want_status, f"expected {want_status}, got {got_status}")
    )

    got_missing = set(_all_missing_items(submitted))
    want_missing = set(expected.get("missing_items") or [])
    if got_missing == want_missing:
        results.append(_r("missing_items_match", 1))
    else:
        parts = []
        if got_missing - want_missing:
            parts.append(f"unexpected: {sorted(got_missing - want_missing)}")
        if want_missing - got_missing:
            parts.append(f"absent: {sorted(want_missing - got_missing)}")
        results.append(_r("missing_items_match", 0, "; ".join(parts)))

    outcomes = {c.get("check_id"): c.get("outcome") for c in submitted.get("checks", [])}
    want_checks = expected.get("critical_checks") or {}
    if want_checks:
        mismatches = [
            f"{cid}: expected {want}, got {outcomes.get(cid)}"
            for cid, want in want_checks.items()
            if outcomes.get(cid) != want
        ]
        score = (len(want_checks) - len(mismatches)) / len(want_checks)
        results.append(_r("critical_checks_match", score, "; ".join(mismatches)))
    else:
        results.append(_r("critical_checks_match", 1, "no critical checks expected"))

    want_tools = expected.get("required_tools") or []
    if want_tools:
        unused = [name for name in want_tools if name not in tool_names]
        score = (len(want_tools) - len(unused)) / len(want_tools)
        results.append(
            _r("required_tools_used", score, f"not called: {unused}" if unused else "")
        )
    else:
        results.append(_r("required_tools_used", 1, "no tools required"))

    citations = _dossier_citations(submitted)
    if not citations:
        results.append(_r("citations_valid", 0, "dossier cites no policy sections"))
    else:
        unknown = sorted({c for c in citations if c not in _section_ids()})
        results.append(
            _r("citations_valid", 0 if unknown else 1, f"unknown section ids: {unknown}" if unknown else "")
        )

    want_citations = expected.get("key_citations") or []
    if not want_citations:
        results.append(_r("key_citations_present", 1, "no key citations expected"))
    else:
        absent = [c for c in want_citations if c not in set(citations)]
        results.append(
            _r("key_citations_present", 0 if absent else 1, f"absent: {absent}" if absent else "")
        )

    violations = []
    if submitted.get("status") == "READY_FOR_UNDERWRITING" and _all_missing_items(submitted):
        violations.append("status READY_FOR_UNDERWRITING but missing_items is non-empty")
    results.append(
        _r("guardrail_ready_without_missing", 0 if violations else 1, "; ".join(violations))
    )

    return results


def deterministic_evaluators(run, example) -> list[dict]:
    """LangSmith evaluator adapter: reads run.outputs and example.outputs."""
    actual = run.outputs if isinstance(run.outputs, dict) else None
    return evaluate(actual, getattr(example, "outputs", None) or {}, error=getattr(run, "error", None))
