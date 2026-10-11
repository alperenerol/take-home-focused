# Eval summary - baseline-v0

Cases: 24 | gate passed: 23/24 | judge grounded: 0.83 (24 judged, mean score 4.83)

## Metrics (mean over cases)

| metric | mean |
|---|---|
| submission_present | 1.00 |
| schema_valid | 1.00 |
| status_match | 0.96 |
| missing_items_match | 0.96 |
| critical_checks_match | 1.00 |
| required_tools_used | 1.00 |
| citations_valid | 1.00 |
| key_citations_present | 1.00 |
| guardrail_ready_without_missing | 1.00 |
| judge_grounded | 0.83 |

## Slices by difficulty

| difficulty | n | status_match | missing_items_match | critical_checks_match |
|---|---|---|---|---|
| boundary | 11 | 1.00 | 1.00 | 1.00 |
| clean | 3 | 1.00 | 1.00 | 1.00 |
| failure | 10 | 0.90 | 0.90 | 1.00 |

## Gate failures

- case-009 (failure): status_match, missing_items_match
