"""LangSmith dataset built from the case fixtures and labels.

One example per case: inputs carry only the case id (the agent fetches its own evidence
through the case-service); outputs carry the expected dossier facts from cases/labels;
metadata carries the slices (category, difficulty) used for before/after reporting.

The dataset is frozen between evaluation-protocol runs (PLAN section 6): uploading to
an existing name is refused unless force=True is passed explicitly.
"""

import json

from langsmith import Client

from src import config

DATASET_NAME = "windmill-bank-cases-v1"
DATASET_DESCRIPTION = (
    "Synthetic Windmill Bank mortgage cases (12 policy sections; 24 cases) with expected "
    "dossier facts for the pre-assessment agent evaluation."
)


def load_labels() -> list[dict]:
    """All case labels, ordered by case id."""
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(config.LABELS_DIR.glob("case-*.json"))
    ]


def build_examples() -> list[dict]:
    """LangSmith example payloads, one per case (deterministic order)."""
    examples = []
    for label in load_labels():
        examples.append(
            {
                "inputs": {"case_id": label["case_id"]},
                "outputs": {
                    "status": label["expected_status"],
                    "missing_items": label["expected_missing_items"],
                    "critical_checks": label["critical_checks"],
                    "key_citations": label["key_citations"],
                    "required_tools": label["required_tools"],
                },
                "metadata": {
                    "case_id": label["case_id"],
                    "title": label["title"],
                    "category": label["category"],
                    "difficulty": label["difficulty"],
                    "assessment_date": label["assessment_date"],
                },
            }
        )
    return examples


def upload(dataset_name: str = DATASET_NAME, *, force: bool = False, client=None) -> str:
    """Upload (or report) the dataset. Returns a human-readable outcome message."""
    client = client or Client()
    if client.has_dataset(dataset_name=dataset_name):
        if not force:
            return (
                f"dataset {dataset_name!r} already exists - left unchanged (frozen "
                "between eval runs). Pass force=True to replace it."
            )
        client.delete_dataset(dataset_name=dataset_name)
    dataset = client.create_dataset(dataset_name, description=DATASET_DESCRIPTION)
    examples = build_examples()
    client.create_examples(dataset_id=dataset.id, examples=examples, max_concurrency=1)
    return f"uploaded {len(examples)} examples to dataset {dataset_name!r}"
