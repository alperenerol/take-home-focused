# POL-INC-02 - Declaration vs Evidence: Income Consistency

Windmill Bank - Underwriting Operations. Section POL-INC-02. Version 1.0. Effective 2026-09-01.

- R1 Compare declared gross annual income (declaration) with evidenced annual income
  (POL-INC-01 R4 or POL-SE-01 R4).
- R2 variance_pct = |declared - evidenced| / evidenced x 100, computed to two decimal places
  (half-up). If variance_pct <= 5.00 the check passes; if greater than 5.00 flag
  EXCEPTION_FLAGGED and state both figures and the variance in the rationale.
- R3 If income cannot be evidenced because evidence is missing, this check cannot pass:
  report ACTION_REQUIRED; do not estimate.

## Boundary

- Exactly 5.00% passes; 5.01% flags.
