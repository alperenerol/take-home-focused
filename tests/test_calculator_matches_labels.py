"""Drive the calculator from every case's inputs and check its verdicts against the
committed labels in cases/labels/.

This keeps three artifacts consistent: the case specs, the expected labels, and the
calculator the agent actually calls. Any drift between them fails here.
"""

import importlib.util
import json
from datetime import date
from pathlib import Path

from src.tools import calculator as calc

ROOT = Path(__file__).resolve().parents[1]


def _load_specs():
    spec = importlib.util.spec_from_file_location("windmill_specs", ROOT / "cases" / "specs.py")
    assert spec is not None and spec.loader is not None, "could not load cases/specs.py"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.CASES


def _prev_months(assessment: date, k: int):
    out = []
    for i in range(1, k + 1):
        m = assessment.month - i
        y = assessment.year
        while m <= 0:
            m += 12
            y -= 1
        out.append(f"{y:04d}-{m:02d}")
    return out


def _tool_args(case):
    docs = case["docs"]
    assessment = date.fromisoformat(case["assessment_date"])
    args = dict(
        loan_amount_gbp=case["loan"]["amount_gbp"],
        property_value_gbp=case["property"]["value_gbp"],
        product_rate_pct=case["loan"]["product_rate_pct"],
        term_months=case["loan"]["term_months"],
        commitments_monthly_gbp=case["commitments"]["monthly_total_gbp"],
        date_of_birth=case["applicant"]["date_of_birth"],
        assessment_date=case["assessment_date"],
    )
    if case["applicant"]["employment_type"] == "employed":
        declared = case["employment"]["declared_annual_income_gbp"]
        months = _prev_months(assessment, 3)
        pays = [d for d in docs if d["kind"] == "payslip" and d["period"] in months]
        if declared is not None:
            args["declared_annual_income_gbp"] = declared
        if len(pays) == 3:
            args["payslip_monthly_grosses"] = [d["gross_gbp"] for d in pays]
    else:
        se = case["self_employment"]
        young = date.fromisoformat(se["business_start_date"]) > date(
            assessment.year - 3, assessment.month, assessment.day
        )
        sas = [d for d in docs if d["kind"] == "sa302"]
        if not young:
            if se["declared_annual_income_gbp"] is not None:
                args["declared_annual_income_gbp"] = se["declared_annual_income_gbp"]
            if len(sas) == 3:
                args["sa302_annual_incomes"] = [d["income_gbp"] for d in sas]
    return args


def test_calculator_reproduces_label_outcomes():
    cases = _load_specs()
    assert cases, "no cases loaded"
    issues = []
    for case in cases:
        cid = case["id"]
        label = json.loads((ROOT / "cases" / "labels" / f"{cid}.json").read_text(encoding="utf-8"))
        checks = label["critical_checks"]
        out = json.loads(calc.mortgage_calculator.invoke(_tool_args(case)))

        if "CHK-LTV" in checks:
            actual_pass = out["ltv_band"] in ("A", "B")
            if (checks["CHK-LTV"] == "PASSED") != actual_pass:
                issues.append(f"{cid}: LTV label {checks['CHK-LTV']} vs band {out['ltv_band']}")

        if "CHK-AFFORDABILITY" in checks:
            expected = checks["CHK-AFFORDABILITY"]
            if expected == "ACTION_REQUIRED":
                if "dti_pct" in out:
                    issues.append(f"{cid}: affordability label ACTION_REQUIRED but DTI computed")
            elif "dti_pct" not in out:
                issues.append(f"{cid}: affordability label {expected} but no DTI computed")
            else:
                actual_pass = out["dti_pass"] and out["stressed_dti_pass"]
                if (expected == "PASSED") != actual_pass:
                    issues.append(
                        f"{cid}: affordability label {expected} vs dti={out['dti_pct']} "
                        f"stressed={out['stressed_dti_pct']} (limit {out['stressed_dti_limit_pct']})"
                    )

        if "CHK-INC-CONSISTENCY" in checks:
            expected = checks["CHK-INC-CONSISTENCY"]
            if expected == "ACTION_REQUIRED":
                if "income_variance_pct" in out:
                    issues.append(f"{cid}: consistency label ACTION_REQUIRED but variance computed")
            elif "income_variance_pct" not in out:
                issues.append(f"{cid}: consistency label {expected} but no variance computed")
            else:
                actual_pass = out["income_within_tolerance"]
                if (expected == "PASSED") != actual_pass:
                    issues.append(
                        f"{cid}: consistency label {expected} vs variance {out['income_variance_pct']}"
                    )

        if "CHK-TERM-AGE" in checks:
            actual_ok = out["term_age_within_maximum"]
            if (checks["CHK-TERM-AGE"] == "PASSED") != actual_ok:
                issues.append(f"{cid}: term-age label {checks['CHK-TERM-AGE']} vs ok={actual_ok}")

    assert not issues, "calculator/label drift:\n" + "\n".join(issues)
