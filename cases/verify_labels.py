"""Authoring-time verification of case labels against the policy rules.

Not part of the agent runtime: this QA pass re-derives each case's expected status, missing
items and key check outcomes from the fixture inputs, using the same numeric conventions as
the policy corpus (half-up rounding to 2dp, stress rate max(product rate + 2.00, 7.00),
90-day recency window, 24/12-month credit windows, term end age 75) and compares them with
the committed labels in cases/labels/.

Run: python cases/verify_labels.py
"""

import json
import sys
from calendar import monthrange
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal, getcontext
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from specs import CASES  # noqa: E402

getcontext().prec = 28
ROOT = Path(__file__).resolve().parent


def r2(x):
    return Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def payment(loan, rate_pct, n):
    r = Decimal(str(rate_pct)) / Decimal(1200)
    f = (1 + r) ** n
    return r2(Decimal(str(loan)) * r / (1 - Decimal(1) / f))


def add_months(d, months):
    m = d.month - 1 + months
    y = d.year + m // 12
    m = m % 12 + 1
    return date(y, m, min(d.day, monthrange(y, m)[1]))


def months_between(a, b):
    """Full calendar months from b to a (a >= b)."""
    m = (a.year - b.year) * 12 + (a.month - b.month)
    if a.day < b.day:
        m -= 1
    return m


def prev_months(ad, k):
    """The k most recent complete months before the assessment date, most recent first."""
    out = []
    for i in range(1, k + 1):
        m = ad.month - i
        y = ad.year
        while m <= 0:
            m += 12
            y -= 1
        out.append(f"{y:04d}-{m:02d}")
    return out


def tax_year_label(start_year):
    return f"{start_year}/{str(start_year + 1)[-2:]}"


def latest_completed_tax_year_start(ad):
    return ad.year - 1 if ad >= date(ad.year, 4, 6) else ad.year - 2


def derive(case, label):
    """Return (status, missing_set, outcomes) derived from evidence; outcomes only for
    checks we can fully derive."""
    ad = date.fromisoformat(case["assessment_date"])
    docs = case["docs"]
    kinds = [d["kind"] for d in docs]
    missing = []
    outcomes = {}
    exceptions_notes = []

    employed = case["applicant"]["employment_type"] == "employed"
    income_incomplete = False
    absent = []  # required documents that are absent (drives CHK-DOC-COMPLETE)

    # ---- document presence / recency ----
    if "id_document" not in kinds:
        missing.append("id_document")
        absent.append("id_document")
    for i, month in enumerate(prev_months(ad, 3), start=1):
        if employed and month not in [d.get("period") for d in docs if d["kind"] == "payslip"]:
            missing.append(f"payslip_month_{i}")
            absent.append(f"payslip_month_{i}")
    letter_doc = next((d for d in docs if d["kind"] == "employer_letter"), None)
    credit_doc = next((d for d in docs if d["kind"] == "credit_report"), None)
    if employed and letter_doc is None:
        missing.append("employer_letter")
        absent.append("employer_letter")
    if credit_doc is None:
        missing.append("credit_report")
        absent.append("credit_report")

    dated = []  # (label, doc) required dated docs for recency
    if employed and letter_doc is not None:
        dated.append(("employer_letter", letter_doc))
    if credit_doc is not None:
        dated.append(("credit_report", credit_doc))
    if employed:
        pays = sorted([d for d in docs if d["kind"] == "payslip"], key=lambda d: d["period"], reverse=True)[:3]
        dated.extend(("payslip", d) for d in pays)
    stale = []
    for _, d in dated:
        if (ad - date.fromisoformat(d["issued"])).days > 90:
            stale.append(d)
    consecutive = all(f"2026-{mm:02d}" in [d.get("period") for d in docs if d["kind"] == "payslip"] for mm in (7, 8, 9)) if employed else True
    recency_bad = bool(stale) or not consecutive
    for d in stale:
        if d["kind"] == "employer_letter":
            if "employer_letter" not in missing:
                missing.append("employer_letter")
        elif d["kind"] == "credit_report":
            if "credit_report" not in missing:
                missing.append("credit_report")
        elif d["kind"] == "payslip":
            idx = prev_months(ad, 3).index(d["period"]) + 1
            tok = f"payslip_month_{idx}"
            if tok not in missing:
                missing.append(tok)
    recency_skipped = not employed and not credit_doc  # not expected in fixtures
    if not recency_skipped:
        outcomes["CHK-DOC-RECENCY"] = "ACTION_REQUIRED" if recency_bad else "PASSED"

    # ---- declaration ----
    declared = case.get("employment", case.get("self_employment", {})).get("declared_annual_income_gbp")
    if declared is None:
        missing.append("declaration_correction")
        absent.append("declaration_correction")

    # ---- income evidence ----
    evidenced = None
    if employed:
        pays = [d for d in docs if d["kind"] == "payslip" and d["period"] in prev_months(ad, 3)]
        if len(pays) == 3:
            evidenced = r2(Decimal(str(sum(d["gross_gbp"] for d in pays) / 3)) * 12)
        else:
            income_incomplete = True
            outcomes["CHK-INC-EMPLOYED"] = "ACTION_REQUIRED"
    else:
        start = latest_completed_tax_year_start(ad)
        targets = [tax_year_label(start - i) for i in range(3)]
        have = {(d["kind"], d["tax_year"]) for d in docs if d["kind"] in ("sa302", "tax_year_overview")}
        young = date.fromisoformat(case["self_employment"]["business_start_date"]) > add_months(ad, -36)
        if young:
            outcomes["CHK-INC-SELFEMPLOYED"] = "EXCEPTION_FLAGGED"
        else:
            yr_missing = []
            for i, ty in enumerate(targets, start=1):
                if ("sa302", ty) not in have:
                    yr_missing.append(f"sa302_year_{i}")
                if ("tax_year_overview", ty) not in have:
                    yr_missing.append(f"tax_year_overview_{i}")
            if yr_missing:
                missing.extend(yr_missing)
                absent.extend(yr_missing)
                outcomes["CHK-INC-SELFEMPLOYED"] = "ACTION_REQUIRED"
            else:
                incomes = [d["income_gbp"] for d in docs if d["kind"] == "sa302"]
                if len(incomes) == 3:
                    evidenced = r2(Decimal(str(sum(incomes) / 3)))
                else:
                    income_incomplete = True
                    outcomes["CHK-INC-SELFEMPLOYED"] = "ACTION_REQUIRED"

    if employed and outcomes.get("CHK-INC-EMPLOYED") is None:
        # employment evidence set complete; check letter content vs payslips
        if letter_doc is None:
            outcomes["CHK-INC-EMPLOYED"] = "ACTION_REQUIRED"
        elif evidenced is not None and letter_doc["salary_gbp"] is not None:
            var = abs(Decimal(str(letter_doc["salary_gbp"])) - evidenced) / evidenced * 100
            outcomes["CHK-INC-EMPLOYED"] = "EXCEPTION_FLAGGED" if r2(var) > 5 else "PASSED"
        else:
            outcomes["CHK-INC-EMPLOYED"] = "PASSED"

    # ---- consistency ----
    if declared is None or evidenced is None:
        outcomes["CHK-INC-CONSISTENCY"] = "ACTION_REQUIRED"
    else:
        var = abs(Decimal(str(declared)) - evidenced) / evidenced * 100
        outcomes["CHK-INC-CONSISTENCY"] = "EXCEPTION_FLAGGED" if r2(var) > 5 else "PASSED"

    # ---- credit markers ----
    if credit_doc is None:
        outcomes["CHK-CREDIT"] = "ACTION_REQUIRED"
    else:
        flag = False
        for m in credit_doc["markers"]:
            if m["type"] == "ccj":
                satisfied = m["status"] == "satisfied"
                age = months_between(ad, date.fromisoformat(m["registered"]))
                if not satisfied or age <= 24:
                    flag = True
            elif m["type"] == "default":
                if months_between(ad, date.fromisoformat(m["registered"])) <= 12:
                    flag = True
        outcomes["CHK-CREDIT"] = "EXCEPTION_FLAGGED" if flag else "PASSED"

    # ---- ltv / affordability / age (need income for affordability) ----
    loan = case["loan"]
    v = r2(Decimal(str(loan["amount_gbp"])) / Decimal(str(case["property"]["value_gbp"])) * 100)
    ltv_band = "A" if v <= 85 else "B" if v <= 90 else "C" if v <= 95 else "D"
    outcomes["CHK-LTV"] = "EXCEPTION_FLAGGED" if ltv_band in ("C", "D") else "PASSED"

    if evidenced is None:
        outcomes["CHK-AFFORDABILITY"] = "ACTION_REQUIRED"
    else:
        pay = payment(loan["amount_gbp"], loan["product_rate_pct"], loan["term_months"])
        comm = case["commitments"]["monthly_total_gbp"]
        mi = evidenced / 12
        dti = r2((pay + Decimal(str(comm))) / mi * 100)
        sr = max(float(loan["product_rate_pct"]) + 2.0, 7.0)
        sp = payment(loan["amount_gbp"], sr, loan["term_months"])
        sdti = r2((sp + Decimal(str(comm))) / mi * 100)
        lim = Decimal(40) if v > 85 else Decimal(45)
        fail = dti > 40 or sdti > lim
        outcomes["CHK-AFFORDABILITY"] = "EXCEPTION_FLAGGED" if fail else "PASSED"

    dob = date.fromisoformat(case["applicant"]["date_of_birth"])
    dob75 = date(dob.year + 75, dob.month, min(dob.day, monthrange(dob.year + 75, dob.month)[1]))
    end = add_months(ad, loan["term_months"])
    outcomes["CHK-TERM-AGE"] = "EXCEPTION_FLAGGED" if end > dob75 else "PASSED"

    # ---- doc complete (any required document absent) ----
    outcomes["CHK-DOC-COMPLETE"] = "ACTION_REQUIRED" if absent else "PASSED"

    # ---- status ----
    has_exception = any(o == "EXCEPTION_FLAGGED" for o in outcomes.values())
    if missing:
        status = "ADDITIONAL_DOCUMENTS_REQUIRED"
    elif has_exception:
        status = "EXPERT_MANUAL_REVIEW_REQUIRED"
    else:
        status = "READY_FOR_UNDERWRITING"

    return status, sorted(set(missing)), outcomes


def main():
    problems = 0
    for case in CASES:
        cid = case["id"]
        label = json.loads((ROOT / "labels" / f"{cid}.json").read_text(encoding="utf-8"))
        n_files = len(list((ROOT / "fixtures" / cid / "evidence").glob("*")))
        if n_files != len(case["docs"]):
            print(f"[{cid}] FAIL evidence files {n_files} != spec docs {len(case['docs'])}")
            problems += 1
            continue

        status, missing, outcomes = derive(case, label)
        issues = []
        if label["expected_status"] != status:
            issues.append(f"status: label {label['expected_status']} vs derived {status}")
        if sorted(label["expected_missing_items"]) != missing:
            issues.append(f"missing: label {sorted(label['expected_missing_items'])} vs derived {missing}")
        for check, exp in label["critical_checks"].items():
            got = outcomes.get(check)
            if got is not None and got != exp:
                issues.append(f"{check}: label {exp} vs derived {got}")

        if issues:
            problems += 1
            print(f"[{cid}] MISMATCH")
            for i in issues:
                print(f"    - {i}")
        else:
            print(f"[{cid}] ok ({status})")

    print()
    if problems:
        print(f"{problems} case(s) with mismatches")
        sys.exit(1)
    print(f"all {len(CASES)} cases verified against policy rules")


if __name__ == "__main__":
    main()
