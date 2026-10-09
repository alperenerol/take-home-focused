"""Render case fixtures and expected labels from cases/specs.py.

Usage: python cases/generate.py   (or: make generate-cases)

Outputs (deterministic; committed for reproducibility):
- cases/fixtures/<case_id>/declaration.json + cases/fixtures/<case_id>/evidence/*.md
- cases/labels/<case_id>.json
"""

import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from specs import CASES  # noqa: E402

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures"
LABELS = ROOT / "labels"

MONTHS = {
    "01": "January", "02": "February", "03": "March", "04": "April",
    "05": "May", "06": "June", "07": "July", "08": "August",
    "09": "September", "10": "October", "11": "November", "12": "December",
}


def month_name(period):
    year, mm = period.split("-")
    return f"{MONTHS[mm]} {year}"


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def money(value):
    return f"GBP {value:,.2f}"


def render_doc(case, doc):
    name = case["applicant"]["full_name"]
    kind = doc["kind"]

    if kind == "payslip":
        return doc, (
            f"# Payslip - {case['employment']['employer']}\n\n"
            f"- Employee: {name}\n"
            f"- Pay period: {month_name(doc['period'])} (monthly)\n"
            f"- Issued: {doc['issued']}\n"
            f"- Gross pay this period: {money(doc['gross_gbp'])}\n"
        )

    if kind == "employer_letter":
        return doc, (
            f"# Employer Letter\n\n"
            f"- Issued: {doc['issued']}\n"
            f"- To: Windmill Bank - Mortgage Operations\n"
            f"- Employer: {case['employment']['employer']}\n"
            f"- Employee: {name}\n"
            f"- Role: {doc['role']}\n"
            f"- Employment type: {doc['employment_type']}\n"
            f"- Gross annual salary: {money(doc['salary_gbp'])}\n\n"
            f"We confirm the above employment details for mortgage assessment purposes.\n"
        )

    if kind == "credit_report":
        lines = []
        for m in doc["markers"]:
            if m["type"] == "ccj":
                s = f"- CCJ ({m['status']}) - registered {m['registered']}"
                if m.get("satisfied_on"):
                    s += f", satisfied {m['satisfied_on']}"
                lines.append(s)
            elif m["type"] == "default":
                s = f"- Default - registered {m['registered']}"
                if m.get("satisfied_on"):
                    s += f", satisfied {m['satisfied_on']}"
                lines.append(s)
        markers = "\n".join(lines) if lines else "None."
        return doc, (
            f"# Credit File Report\n\n"
            f"- Issued: {doc['issued']}\n"
            f"- Agency: Credia (synthetic)\n"
            f"- Applicant: {name}\n\n"
            f"## Registered markers\n\n"
            f"{markers}\n"
        )

    if kind == "id_document":
        holder = doc.get("holder") or name
        return doc, (
            f"# Photo ID (copy)\n\n"
            f"- Type: {doc['type']}\n"
            f"- Holder: {holder}\n"
            f"- Valid to: {doc['valid_to']}\n"
        )

    if kind == "sa302":
        return doc, (
            f"# SA302 Tax Calculation - {doc['tax_year']}\n\n"
            f"- Applicant: {name}\n"
            f"- Business: {case['self_employment']['business_name']}\n"
            f"- Tax year: {doc['tax_year']}\n"
            f"- Total taxable income: {money(doc['income_gbp'])}\n"
        )

    if kind == "tax_year_overview":
        return doc, (
            f"# HMRC Tax Year Overview - {doc['tax_year']}\n\n"
            f"- Issued: {doc['issued']}\n"
            f"- Tax year: {doc['tax_year']}\n"
            f"- Status: total tax due paid in full\n"
        )

    if kind == "noise_document":
        body = "\n".join(doc["lines"])
        return doc, f"# {doc['title']}\n\n{body}\n"

    raise ValueError(f"unknown doc kind: {kind}")


def doc_filename(doc):
    kind = doc["kind"]
    if kind == "payslip":
        return f"payslip_{doc['period']}.md"
    if kind == "id_document":
        return "id_document.md"
    if kind == "employer_letter":
        return "employer_letter.md"
    if kind == "credit_report":
        return "credit_report.md"
    if kind == "sa302":
        return f"sa302_{doc['tax_year'].replace('/', '-')}.md"
    if kind == "tax_year_overview":
        return f"tax_year_overview_{doc['tax_year'].replace('/', '-')}.md"
    if kind == "noise_document":
        return f"{slug(doc['title'])}.md"
    raise ValueError(f"unknown doc kind: {kind}")


def write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    ids = set()
    for case in CASES:
        cid = case["id"]
        assert cid not in ids, f"duplicate case id: {cid}"
        ids.add(cid)

        case_dir = FIXTURES / cid
        if case_dir.exists():
            shutil.rmtree(case_dir)
        (case_dir / "evidence").mkdir(parents=True)

        declaration = {
            "case_id": cid,
            "assessment_date": case["assessment_date"],
            "applicant": case["applicant"],
        }
        if "employment" in case:
            declaration["employment"] = case["employment"]
        if "self_employment" in case:
            declaration["self_employment"] = case["self_employment"]
        declaration["property"] = case["property"]
        declaration["loan"] = case["loan"]
        declaration["commitments"] = case["commitments"]
        write_json(case_dir / "declaration.json", declaration)

        filenames = set()
        for doc in case["docs"]:
            fname = doc_filename(doc)
            assert fname not in filenames, f"{cid}: duplicate evidence filename {fname}"
            filenames.add(fname)
            _, text = render_doc(case, doc)
            (case_dir / "evidence" / fname).write_text(text, encoding="utf-8")

        expected = case["expected"]
        label = {
            "case_id": cid,
            "title": case["title"],
            "category": case["category"],
            "difficulty": case["difficulty"],
            "assessment_date": case["assessment_date"],
            "expected_status": expected["status"],
            "expected_missing_items": expected["missing_items"],
            "critical_checks": expected["critical_checks"],
            "key_citations": expected["key_citations"],
            "required_tools": expected["required_tools"],
            "notes": expected["notes"],
        }
        write_json(LABELS / f"{cid}.json", label)

        n_docs = len(case["docs"])
        print(f"{cid}: {n_docs} evidence docs, status {expected['status']}")

    # remove stale labels for cases that no longer exist
    for stale in LABELS.glob("case-*.json"):
        if stale.stem not in ids:
            stale.unlink()

    print(f"\ngenerated {len(CASES)} fixtures and {len(CASES)} labels")


if __name__ == "__main__":
    main()
