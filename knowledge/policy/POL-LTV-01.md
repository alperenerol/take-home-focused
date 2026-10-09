# POL-LTV-01 - Loan-to-Value Bands

Windmill Bank - Underwriting Operations. Section POL-LTV-01. Version 1.0. Effective 2026-09-01.

- R1 LTV = loan amount / property value x 100, rounded to two decimal places (half-up).
- R2 Bands:
  - A: LTV <= 85.00
  - B: 85.00 < LTV <= 90.00
  - C: 90.00 < LTV <= 95.00
  - D: LTV > 95.00
- R3 Band A: standard. Band B: standard, but note it as a higher-LTV case in the rationale;
  the stricter affordability limit in POL-AFF-01 R5 applies.
- R4 Band C: flag EXCEPTION_FLAGGED and require expert manual review (high-LTV sign-off).
- R5 Band D: above the 95.00 maximum. Flag EXCEPTION_FLAGGED, refer for expert manual review,
  and state in the required action that the maximum LTV is 95.00.
