"""Structured dossier schema for the assessment agent.

Enums mirror the case-service vocabularies in src/mcp_server/case_service.py
(kept in sync by tests/test_schemas.py). Used as the agent's response_format and to
validate dossiers in the eval harness.
"""

from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class DossierStatus(str, Enum):
    READY = "READY_FOR_UNDERWRITING"
    ADDITIONAL_DOCUMENTS_REQUIRED = "ADDITIONAL_DOCUMENTS_REQUIRED"
    EXPERT_MANUAL_REVIEW_REQUIRED = "EXPERT_MANUAL_REVIEW_REQUIRED"


class CheckOutcome(str, Enum):
    PASSED = "PASSED"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    EXCEPTION_FLAGGED = "EXCEPTION_FLAGGED"


class CheckId(str, Enum):
    DOC_COMPLETE = "CHK-DOC-COMPLETE"
    DOC_RECENCY = "CHK-DOC-RECENCY"
    INC_EMPLOYED = "CHK-INC-EMPLOYED"
    INC_SELFEMPLOYED = "CHK-INC-SELFEMPLOYED"
    INC_CONSISTENCY = "CHK-INC-CONSISTENCY"
    CREDIT = "CHK-CREDIT"
    LTV = "CHK-LTV"
    AFFORDABILITY = "CHK-AFFORDABILITY"
    TERM_AGE = "CHK-TERM-AGE"


class Check(BaseModel):
    """One policy check applied to the case."""

    check_id: CheckId = Field(description="The check's id from POL-STAT-01.")
    outcome: CheckOutcome = Field(
        description=(
            "PASSED when the evidence satisfies the rule; ACTION_REQUIRED when something "
            "must be provided or corrected; EXCEPTION_FLAGGED when the rule is breached, "
            "documents contradict, or expert review is required."
        )
    )
    rationale: str = Field(
        description="Why this outcome follows, naming the figures used and the policy section ids."
    )
    citations: List[str] = Field(
        description="Policy section ids the rule comes from, e.g. ['POL-AFF-01']."
    )
    missing_items: List[str] = Field(
        description=(
            "Exact missing-item tokens for this check (e.g. payslip_month_1, employer_letter); "
            "empty list when none."
        )
    )


class Dossier(BaseModel):
    """The assessment dossier submitted for one case."""

    case_id: str = Field(description="The case id, e.g. 'case-001'.")
    status: DossierStatus = Field(
        description=(
            "ADDITIONAL_DOCUMENTS_REQUIRED if any check reports missing items; otherwise "
            "EXPERT_MANUAL_REVIEW_REQUIRED if any check is EXCEPTION_FLAGGED; otherwise "
            "READY_FOR_UNDERWRITING. Missing items take precedence."
        )
    )
    checks: List[Check] = Field(description="One entry per applicable check.")
    required_actions: List[str] = Field(
        description="Concrete next steps for the operation; empty list when none."
    )
    summary: str = Field(description="Short summary for an underwriter (1-3 sentences).")
