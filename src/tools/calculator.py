"""Deterministic mortgage math for Windmill Bank assessments.

Implements exactly the numeric conventions used by the policy corpus and the case
labels (half-up rounding to 2 decimal places, stress rate = max(product rate +
2.00, 7.00), DTI <= 40.00, stressed DTI <= 45.00 tightened to <= 40.00 above
85% LTV, LTV bands A <= 85 / B <= 90 / C <= 95 / D > 95, term end age <= 75).

Thresholds mirror POL-LTV-01, POL-AFF-01 and POL-AGE-01; if the corpus changes,
update both together. The agent-facing tool is `mortgage_calculator`; the plain
functions below are used directly by unit tests.
"""

import json
from calendar import monthrange
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from langchain_core.tools import tool

DTI_LIMIT_PCT = Decimal("40.00")
STRESSED_DTI_LIMIT_PCT = Decimal("45.00")
STRESSED_DTI_LIMIT_HIGH_LTV_PCT = Decimal("40.00")  # applies when LTV > 85.00
LTV_MAXIMUM_PCT = Decimal("95.00")
STRESS_BUFFER_PCT = Decimal("2.00")
STRESS_RATE_FLOOR_PCT = Decimal("7.00")
INCOME_VARIANCE_TOLERANCE_PCT = Decimal("5.00")
TERM_AGE_MAX_YEARS = 75


def _d(value) -> Decimal:
    return Decimal(str(value))


def r2(value) -> Decimal:
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def monthly_payment(loan_amount_gbp, annual_rate_pct, term_months: int) -> Decimal:
    """Annuity payment: P*r / (1 - (1+r)^-n), r = annual rate / 12 / 100."""
    r = _d(annual_rate_pct) / Decimal(1200)
    n = int(term_months)
    factor = (1 + r) ** n
    return r2(_d(loan_amount_gbp) * r / (1 - Decimal(1) / factor))


def loan_to_value_pct(loan_amount_gbp, property_value_gbp) -> Decimal:
    return r2(_d(loan_amount_gbp) / _d(property_value_gbp) * 100)


def ltv_band(ltv_pct) -> str:
    v = r2(_d(ltv_pct))
    if v <= 85:
        return "A"
    if v <= 90:
        return "B"
    if v <= 95:
        return "C"
    return "D"


def stressed_rate_pct(product_rate_pct) -> Decimal:
    return max(r2(_d(product_rate_pct) + STRESS_BUFFER_PCT), STRESS_RATE_FLOOR_PCT)


def debt_to_income_pct(payment_gbp, commitments_monthly_gbp, monthly_income_gbp) -> Decimal:
    return r2(
        (_d(payment_gbp) + _d(commitments_monthly_gbp)) / _d(monthly_income_gbp) * 100
    )


def income_variance_pct(declared_annual_gbp, evidenced_annual_gbp) -> Decimal:
    return r2(
        abs(_d(declared_annual_gbp) - _d(evidenced_annual_gbp))
        / _d(evidenced_annual_gbp)
        * 100
    )


def add_months(start: date, months: int) -> date:
    m = start.month - 1 + months
    y = start.year + m // 12
    m = m % 12 + 1
    return date(y, m, min(start.day, monthrange(y, m)[1]))


def term_end_date(assessment_date: str, term_months: int) -> date:
    return add_months(date.fromisoformat(assessment_date), int(term_months))


def term_end_age_within_max(assessment_date: str, term_months: int, date_of_birth: str) -> bool:
    """Calendar comparison: term end must be on or before the 75th birthday."""
    dob = date.fromisoformat(date_of_birth)
    dob75 = date(dob.year + TERM_AGE_MAX_YEARS, dob.month, min(dob.day, monthrange(dob.year + TERM_AGE_MAX_YEARS, dob.month)[1]))
    return term_end_date(assessment_date, term_months) <= dob75


def term_end_age_years(assessment_date: str, term_months: int, date_of_birth: str) -> Decimal:
    """Display-only approximation (days / 365.25); the pass/fail rule is calendar-based."""
    end = term_end_date(assessment_date, term_months)
    days = (end - date.fromisoformat(date_of_birth)).days
    return r2(_d(days) / _d("365.25"))


def _resolve_income(
    payslip_monthly_grosses, sa302_annual_incomes, monthly_income_gbp
):
    """Return (evidenced_annual, assessed_monthly, how), declared-agnostic.

    Conventions: POL-INC-01 R4 (payslips: mean monthly gross x 12, 2dp half-up);
    POL-SE-01 R4 (SA302: mean of annual incomes, 2dp half-up). The monthly figure
    used for DTI is the evidenced annual income / 12 (POL-AFF-01 R4).
    """
    if payslip_monthly_grosses:
        values = [_d(v) for v in payslip_monthly_grosses]
        annual = r2(sum(values) / len(values) * 12)
        return annual, annual / 12, "mean monthly gross x 12 (POL-INC-01 R4)"
    if sa302_annual_incomes:
        values = [_d(v) for v in sa302_annual_incomes]
        annual = r2(sum(values) / len(values))
        return annual, annual / 12, "mean of SA302 incomes (POL-SE-01 R4)"
    if monthly_income_gbp:
        annual = r2(_d(monthly_income_gbp) * 12)
        return annual, annual / 12, "monthly income x 12"
    return None, None, None


@tool
def mortgage_calculator(
    loan_amount_gbp: float,
    property_value_gbp: float,
    product_rate_pct: float,
    term_months: int,
    payslip_monthly_grosses: list[float] | None = None,
    sa302_annual_incomes: list[float] | None = None,
    monthly_income_gbp: float | None = None,
    commitments_monthly_gbp: float = 0.0,
    declared_annual_income_gbp: float | None = None,
    date_of_birth: str | None = None,
    assessment_date: str | None = None,
) -> str:
    """Deterministic mortgage calculations for one Windmill Bank case. Use this instead
    of doing arithmetic yourself. Provide the case numbers as they appear in the
    declaration and evidence; do not round or pre-process them.

    Income: pass `payslip_monthly_grosses` (the gross figures from the payslips that
    count towards the income assessment) or `sa302_annual_incomes` (for self-employed
    cases) or `monthly_income_gbp`. Pass `declared_annual_income_gbp` as well to get
    the declaration-vs-evidence variance and its 5% tolerance verdict.

    Returns JSON with: loan_to_value_pct, ltv_band, ltv_within_maximum;
    product and stressed monthly payments and stressed rate; evidenced annual income
    and monthly income used; income_variance_pct and income_within_tolerance (when
    declared income is given); dti_pct and stressed_dti_pct with their limits and
    pass verdicts (the stressed limit tightens to 40 when LTV is above 85);
    term_end_date, term_end_age_years and term_age_within_maximum (when date_of_birth
    and assessment_date are given); and policy_refs naming the sections the verdicts
    come from. All money and percentage figures are strings rounded half-up to 2dp.
    """
    try:
        loan = _d(loan_amount_gbp)
        value = _d(property_value_gbp)
        term = int(term_months)
        if loan <= 0 or value <= 0 or term <= 0:
            raise ValueError("loan_amount_gbp, property_value_gbp and term_months must be positive")
        rate = _d(product_rate_pct)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid numeric input: {exc}") from exc

    out: dict = {}
    policy_refs: list[str] = []

    ltv = loan_to_value_pct(loan, value)
    band = ltv_band(ltv)
    out["loan_to_value_pct"] = str(ltv)
    out["ltv_band"] = band
    out["ltv_within_maximum"] = ltv <= LTV_MAXIMUM_PCT
    policy_refs.append("POL-LTV-01")

    pay = monthly_payment(loan, rate, term)
    sr = stressed_rate_pct(rate)
    spay = monthly_payment(loan, sr, term)
    out["product_monthly_payment_gbp"] = str(pay)
    out["stressed_rate_pct"] = str(sr)
    out["stressed_monthly_payment_gbp"] = str(spay)

    evidenced, monthly_used, how = _resolve_income(
        payslip_monthly_grosses, sa302_annual_incomes, monthly_income_gbp
    )
    if evidenced is not None:
        out["evidenced_annual_income_gbp"] = str(evidenced)
        out["assessed_monthly_income_gbp"] = str(r2(monthly_used))
        out["income_basis"] = how
        policy_refs.extend(["POL-INC-01", "POL-INC-02"])
    if evidenced is not None and declared_annual_income_gbp is not None:
        var = income_variance_pct(declared_annual_income_gbp, evidenced)
        out["income_variance_pct"] = str(var)
        out["income_within_tolerance"] = var <= INCOME_VARIANCE_TOLERANCE_PCT
    if monthly_used is not None:
        comm = _d(commitments_monthly_gbp)
        dti = debt_to_income_pct(pay, comm, monthly_used)
        sdti = debt_to_income_pct(spay, comm, monthly_used)
        s_limit = STRESSED_DTI_LIMIT_HIGH_LTV_PCT if ltv > 85 else STRESSED_DTI_LIMIT_PCT
        out["dti_pct"] = str(dti)
        out["dti_limit_pct"] = str(DTI_LIMIT_PCT)
        out["dti_pass"] = dti <= DTI_LIMIT_PCT
        out["stressed_dti_pct"] = str(sdti)
        out["stressed_dti_limit_pct"] = str(s_limit)
        out["stressed_dti_pass"] = sdti <= s_limit
        out["commitments_monthly_gbp"] = str(r2(comm))
        policy_refs.append("POL-AFF-01")

    if date_of_birth and assessment_date:
        try:
            end = term_end_date(assessment_date, term)
            out["term_end_date"] = end.isoformat()
            out["term_end_age_years"] = str(term_end_age_years(assessment_date, term, date_of_birth))
            out["term_age_within_maximum"] = term_end_age_within_max(assessment_date, term, date_of_birth)
            policy_refs.append("POL-AGE-01")
        except ValueError:
            out["term_end_date"] = None
            out["term_age_note"] = "could not parse date_of_birth or assessment_date (use YYYY-MM-DD)"

    out["policy_refs"] = sorted(set(policy_refs))
    return json.dumps(out, indent=2)
