"""Unit tests for the deterministic mortgage calculator.

Expected values are the policy-correct figures for the committed case fixtures
(cross-checked by cases/verify_labels.py and tests/test_calculator_matches_labels.py).
"""

import json

from src.tools import calculator as calc


def test_monthly_payment_known_rows():
    assert str(calc.monthly_payment(220000, 4.5, 300)) == "1222.83"
    assert str(calc.monthly_payment(270000, 4.4, 300)) == "1485.46"
    assert str(calc.monthly_payment(258000, 7.0, 300)) == "1823.49"
    assert str(calc.monthly_payment(244000, 7.5, 300)) == "1803.14"
    assert str(calc.monthly_payment(180000, 3.5, 300)) == "901.12"
    assert str(calc.monthly_payment(200000, 4.5, 132)) == "1923.75"


def test_stressed_rate_floor_and_buffer():
    assert str(calc.stressed_rate_pct(4.5)) == "7.00"  # 6.5 floored
    assert str(calc.stressed_rate_pct(5.5)) == "7.50"  # buffer, above floor
    assert str(calc.stressed_rate_pct(5.0)) == "7.00"  # exactly at floor
    assert str(calc.stressed_rate_pct(4.9)) == "7.00"


def test_ltv_values_and_bands():
    assert str(calc.loan_to_value_pct(220000, 320000)) == "68.75"
    assert str(calc.loan_to_value_pct(258000, 300000)) == "86.00"
    assert str(calc.loan_to_value_pct(270000, 300000)) == "90.00"
    assert str(calc.loan_to_value_pct(285000, 300000)) == "95.00"
    assert str(calc.loan_to_value_pct(286500, 300000)) == "95.50"

    assert calc.ltv_band(85.00) == "A"  # inclusive upper bound
    assert calc.ltv_band("85.01") == "B"
    assert calc.ltv_band(86.00) == "B"
    assert calc.ltv_band(90.00) == "B"  # inclusive upper bound
    assert calc.ltv_band("90.01") == "C"
    assert calc.ltv_band(95.00) == "C"  # inclusive upper bound
    assert calc.ltv_band("95.01") == "D"


def test_income_variance_and_tolerance():
    assert str(calc.income_variance_pct(50400, 48000)) == "5.00"  # boundary passes
    assert str(calc.income_variance_pct(51000, 48000)) == "6.25"
    assert str(calc.income_variance_pct(58000, 51960)) == "11.62"
    # half-up rounding probe: 4.375 -> 4.38 (a float round() would give 4.37)
    assert str(calc.income_variance_pct(50100, 48000)) == "4.38"


def test_term_age_boundary():
    # 132 months from assessment ends after the 75th birthday (case-021)
    assert calc.term_end_date("2026-10-01", 132).isoformat() == "2037-10-01"
    assert str(calc.term_end_age_years("2026-10-01", 132, "1962-03-15")) == "75.55"
    assert calc.term_end_age_within_max("2026-10-01", 132, "1962-03-15") is False
    # exactly on the 75th birthday: passes (<= 75y 0d)
    assert calc.term_end_date("2026-10-01", 396).isoformat() == "2059-10-01"
    assert calc.term_end_age_within_max("2026-10-01", 396, "1984-10-01") is True


def test_tool_case_016_tightened_limit():
    out = json.loads(
        calc.mortgage_calculator.invoke(
            {
                "loan_amount_gbp": 258000,
                "property_value_gbp": 300000,
                "product_rate_pct": 5.0,
                "term_months": 300,
                "payslip_monthly_grosses": [5000, 5000, 5000],
                "commitments_monthly_gbp": 300,
                "declared_annual_income_gbp": 60000,
                "date_of_birth": "1983-08-14",
                "assessment_date": "2026-10-01",
            }
        )
    )
    assert out["loan_to_value_pct"] == "86.00"
    assert out["ltv_band"] == "B"
    assert out["dti_pct"] == "36.16"
    assert out["dti_pass"] is True
    assert out["stressed_dti_pct"] == "42.47"
    assert out["stressed_dti_limit_pct"] == "40.00"  # LTV > 85 tightening
    assert out["stressed_dti_pass"] is False
    assert out["income_variance_pct"] == "0.00"
    assert out["term_age_within_maximum"] is True
    assert out["term_end_age_years_and_days"] == "68 years and 48 days"
    assert "POL-AFF-01" in out["policy_refs"]


def test_tool_case_019_stressed_fail_at_standard_limit():
    out = json.loads(
        calc.mortgage_calculator.invoke(
            {
                "loan_amount_gbp": 244000,
                "property_value_gbp": 340000,
                "product_rate_pct": 5.5,
                "term_months": 300,
                "payslip_monthly_grosses": [5000, 5000, 5000],
                "commitments_monthly_gbp": 480,
                "declared_annual_income_gbp": 60000,
                "date_of_birth": "1985-10-11",
                "assessment_date": "2026-10-01",
            }
        )
    )
    assert out["dti_pct"] == "39.57"
    assert out["dti_pass"] is True
    assert out["stressed_dti_limit_pct"] == "45.00"
    assert out["stressed_dti_pct"] == "45.66"
    assert out["stressed_dti_pass"] is False


def test_tool_without_income_omits_affordability():
    out = json.loads(
        calc.mortgage_calculator.invoke(
            {
                "loan_amount_gbp": 220000,
                "property_value_gbp": 320000,
                "product_rate_pct": 4.5,
                "term_months": 300,
            }
        )
    )
    assert "dti_pct" not in out
    assert "stressed_dti_pct" not in out
    assert out["loan_to_value_pct"] == "68.75"
    assert out["product_monthly_payment_gbp"] == "1222.83"  # still computable


def test_term_end_age_years_days_convention():
    # case-001: dob 1990-04-12, assessment 2026-10-01, 300 months -> end 2051-10-01
    assert calc.term_end_age_years_days("2026-10-01", 300, "1990-04-12") == "61 years and 172 days"
    # case-021: end 2037-10-01 for dob 1962-03-15 -> beyond 75 years and 0 days
    assert calc.term_end_age_years_days("2026-10-01", 132, "1962-03-15") == "75 years and 200 days"
    # exactly on the 75th birthday (POL-AGE-01 R1: passes at 75 years and 0 days)
    assert calc.term_end_age_years_days("2026-10-01", 396, "1984-10-01") == "75 years and 0 days"
    # 29 February dob on a non-leap anchor year falls back to 28 February
    assert calc.term_end_age_years_days("2024-10-01", 5, "2000-02-29") == "25 years and 1 day"
