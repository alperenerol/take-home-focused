# Cases

Synthetic case fixtures for the pre-assessment agent, generated deterministically from
`specs.py`.

| File | Role |
| --- | --- |
| `specs.py` | Source of truth: declaration inputs, evidence documents, expected labels |
| `generate.py` | Renders `fixtures/<case_id>/` (declaration + evidence) and `labels/<case_id>.json` |
| `verify_labels.py` | QA: re-derives every expected outcome from the inputs against the policy rules |
| `fixtures/` | Committed outputs: 24 cases, each `declaration.json` + `evidence/*.md` |
| `labels/` | Committed expected outcomes: status, missing items, critical checks, citations, required tools |

Regenerate and verify:

    make generate-cases
    make verify-labels

Coverage: clean passes, missing evidence, recency boundaries (89/90/91 days), self-employed
(two of three years vs startup), income variance (5.00% boundary), credit markers
(recent/old/unsatisfied CCJ and defaults), LTV boundaries (85/90/95 and above the maximum),
affordability edges (DTI 40 / stressed 45, higher-LTV tightening), term age, contradictory
documents, malformed declaration, and missing-item-vs-exception precedence.

All content is fully synthetic and self-authored for this exercise.
