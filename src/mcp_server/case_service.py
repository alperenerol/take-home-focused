"""Windmill Bank case-service: the MCP server the assessment agent acts through.

Exposes two tools over stdio (FastMCP):

- get_case_files(case_id): the applicant declaration plus every evidence document
  for one case, as JSON. This is how the agent reads a case.
- submit_dossier(case_id, dossier): the trusted action. The dossier is validated
  (shape, identity, enums) and stored under submitted/<run_id>/.

Run standalone for debugging:  python src/mcp_server/case_service.py
The agent reaches it through src/tools/mcp_case_service.py (langchain.mcp).

Boundary: this server enforces shape, identity and enums only. Policy semantics
(statuses, missing-item logic, rule outcomes) are the agent's responsibility and are
graded against cases/labels in the evals - the server stores what it is given, it never
rewrites a dossier. The enum vocabularies here are the canonical ones; the Pydantic
dossier schema in the agent mirrors them.
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = Path(os.environ.get("WINDMILL_FIXTURES_DIR", REPO_ROOT / "cases" / "fixtures"))
SUBMITTED_ROOT = Path(os.environ.get("WINDMILL_SUBMITTED_DIR", REPO_ROOT / "submitted"))

CASE_ID_RE = re.compile(r"^case-\d{3}$")
CITATION_RE = re.compile(r"^POL-[A-Z]+-\d{2}$")

STATUSES = (
    "READY_FOR_UNDERWRITING",
    "ADDITIONAL_DOCUMENTS_REQUIRED",
    "EXPERT_MANUAL_REVIEW_REQUIRED",
)
OUTCOMES = ("PASSED", "ACTION_REQUIRED", "EXCEPTION_FLAGGED")
CHECK_IDS = (
    "CHK-DOC-COMPLETE",
    "CHK-DOC-RECENCY",
    "CHK-INC-EMPLOYED",
    "CHK-INC-SELFEMPLOYED",
    "CHK-INC-CONSISTENCY",
    "CHK-CREDIT",
    "CHK-LTV",
    "CHK-AFFORDABILITY",
    "CHK-TERM-AGE",
)

mcp = FastMCP(name="windmill-case-service")


def _case_dir(case_id: str) -> Path:
    if not isinstance(case_id, str) or not CASE_ID_RE.match(case_id):
        raise ValueError(f"invalid case_id {case_id!r}: expected the form 'case-001'")
    case_dir = FIXTURES_DIR / case_id
    if not case_dir.is_dir():
        raise ValueError(f"unknown case_id {case_id!r}: no fixtures directory at {case_dir}")
    return case_dir


def get_case_files(case_id: str) -> str:
    """Return the complete file set for one mortgage case: the applicant declaration
    (JSON) and every evidence document (markdown, keyed by filename). Read the
    declaration and all evidence documents before assessing. case_id has the form
    'case-001'.
    """
    case_dir = _case_dir(case_id)
    declaration = json.loads((case_dir / "declaration.json").read_text(encoding="utf-8"))
    evidence = {}
    for path in sorted((case_dir / "evidence").glob("*.md")):
        evidence[path.name] = path.read_text(encoding="utf-8")
    return json.dumps(
        {
            "case_id": case_id,
            "declaration": declaration,
            "evidence_files": evidence,
            "evidence_file_count": len(evidence),
        },
        indent=2,
    )


def _dossier_problems(case_id: str, dossier: Any) -> list[str]:
    if not isinstance(dossier, dict):
        return ["dossier must be an object"]
    problems = []
    for key in ("case_id", "status", "checks", "required_actions", "summary"):
        if key not in dossier:
            problems.append(f"missing required key: {key}")
    if dossier.get("case_id") != case_id:
        problems.append(f"dossier.case_id must equal {case_id!r} (got {dossier.get('case_id')!r})")
    if dossier.get("status") not in STATUSES:
        problems.append(f"status must be one of {list(STATUSES)} (got {dossier.get('status')!r})")
    checks = dossier.get("checks")
    if not isinstance(checks, list) or not checks:
        problems.append("checks must be a non-empty list")
    else:
        for i, check in enumerate(checks):
            where = f"checks[{i}]"
            if not isinstance(check, dict):
                problems.append(f"{where} must be an object")
                continue
            if check.get("check_id") not in CHECK_IDS:
                problems.append(f"{where}.check_id must be one of the CHK- ids (got {check.get('check_id')!r})")
            if check.get("outcome") not in OUTCOMES:
                problems.append(f"{where}.outcome must be one of {list(OUTCOMES)} (got {check.get('outcome')!r})")
            rationale = check.get("rationale")
            if not isinstance(rationale, str) or not rationale.strip():
                problems.append(f"{where}.rationale must be a non-empty string")
            citations = check.get("citations")
            if not isinstance(citations, list) or not all(
                isinstance(c, str) and CITATION_RE.match(c) for c in citations
            ):
                problems.append(f"{where}.citations must be a list of section ids like 'POL-AFF-01'")
            if not isinstance(check.get("missing_items"), list):
                problems.append(f"{where}.missing_items must be a list (use [] when none)")
    if not isinstance(dossier.get("required_actions"), list) or not all(
        isinstance(a, str) for a in dossier.get("required_actions", [])
    ):
        problems.append("required_actions must be a list of strings (use [] when none)")
    if not isinstance(dossier.get("summary"), str) or not dossier.get("summary", "").strip():
        problems.append("summary must be a non-empty string")
    return problems


def submit_dossier(case_id: str, dossier: dict[str, Any]) -> str:
    """Submit the final assessment dossier for a case. This is the trusted action the
    assessment ends with. The dossier is validated (shape, identity, enums) and stored
    under submitted/<run_id>/; it is never modified. Call get_case_files and apply the
    policy first. Pass the complete dossier object with keys: case_id, status
    (READY_FOR_UNDERWRITING | ADDITIONAL_DOCUMENTS_REQUIRED | EXPERT_MANUAL_REVIEW_REQUIRED),
    checks (list of objects: check_id (CHK- ids), outcome (PASSED | ACTION_REQUIRED |
    EXCEPTION_FLAGGED), rationale, citations (policy section ids), missing_items),
    required_actions (list of strings), summary.
    """
    _case_dir(case_id)
    problems = _dossier_problems(case_id, dossier)
    if problems:
        raise ValueError("dossier rejected: " + "; ".join(problems))

    run_id = os.environ.get("WINDMILL_RUN_ID", "local")
    target_dir = SUBMITTED_ROOT / run_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{case_id}.json"
    stored = {
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "dossier": dossier,
    }
    target.write_text(json.dumps(stored, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return (
        f"dossier accepted and stored for {case_id} (run {run_id}): "
        f"status={dossier['status']}, checks={len(dossier['checks'])}"
    )


mcp.tool(name="get_case_files")(get_case_files)
mcp.tool(name="submit_dossier")(submit_dossier)


if __name__ == "__main__":
    mcp.run(show_banner=False)
