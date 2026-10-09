# POL-AFF-01 - Affordability (DTI and Stress)

Windmill Bank - Underwriting Operations. Section POL-AFF-01. Version 1.0. Effective 2026-09-01.

## Inputs

- R1 Use: evidenced gross annual income (POL-INC-01 R4 or POL-SE-01 R4), loan amount,
  product rate (% per annum), term (months) and declared monthly commitments.

## Payments

- R2 Product monthly payment = P x r / (1 - (1 + r)^-n), where P is the loan amount, r is the
  product rate / 12 / 100, and n is the term in months. Compute to the nearest penny.
- R3 Stressed monthly payment uses the stress rate = product rate + 2.00 percentage points,
  floored at 7.00% per annum, under the same formula.

## Ratios

- R4 DTI percent = (product payment + monthly commitments) / (evidenced annual income / 12)
  x 100, computed to two decimal places (half-up). Pass if and only if <= 40.00.
- R5 Stressed DTI uses the stressed payment. Pass if and only if <= 45.00; however, for
  LTV greater than 85.00 (POL-LTV-01) the stressed limit is 40.00 (higher-LTV tightening).
- R6 If income is not evidenced, this check cannot pass: report ACTION_REQUIRED; do not
  estimate payments or ratios from assumed income.

## Boundary

- A ratio exactly on a limit passes; any amount above fails.
