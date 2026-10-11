# Diff v1 -> v2

Cases: 24 -> 28 | gate passed: 24/24 -> 28/28 | judge grounded: 1.00 -> 0.96

| metric | v1 | v2 | delta |
|---|---|---|---|
| submission_present | 1.00 | 1.00 | +0.00 |
| schema_valid | 1.00 | 1.00 | +0.00 |
| status_match | 1.00 | 1.00 | +0.00 |
| missing_items_match | 1.00 | 1.00 | +0.00 |
| critical_checks_match | 1.00 | 1.00 | -0.00 |
| required_tools_used | 1.00 | 1.00 | +0.00 |
| citations_valid | 1.00 | 1.00 | +0.00 |
| key_citations_present | 0.96 | 0.96 | +0.01 |
| guardrail_ready_without_missing | 1.00 | 1.00 | +0.00 |
| judge_grounded | 1.00 | 0.96 | -0.04 |

## Slices by difficulty (status_match / missing_items_match / critical_checks_match)

| difficulty | v1 | v2 |
|---|---|---|
| adversarial | - | 1.00 / 1.00 / 0.97 |
| boundary | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| clean | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| failure | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
