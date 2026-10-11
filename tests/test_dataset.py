"""Dataset build tests (offline) plus the upload flow against a fake client."""

import json

from evals import dataset
from src import config

# The dataset is versioned (v2 = v1's 24 cases plus the 4 adversarial cases).
EXPECTED_CASES = 28


def test_build_examples_covers_all_cases():
    examples = dataset.build_examples()
    assert len(examples) == EXPECTED_CASES
    ids = [e["inputs"]["case_id"] for e in examples]
    assert ids == sorted(ids)
    assert len(set(ids)) == EXPECTED_CASES


def test_examples_match_labels():
    examples = {e["inputs"]["case_id"]: e for e in dataset.build_examples()}
    for path in sorted(config.LABELS_DIR.glob("case-*.json")):
        label = json.loads(path.read_text(encoding="utf-8"))
        example = examples[label["case_id"]]
        assert example["outputs"]["status"] == label["expected_status"]
        assert example["outputs"]["missing_items"] == label["expected_missing_items"]
        assert example["outputs"]["critical_checks"] == label["critical_checks"]
        assert example["outputs"]["key_citations"] == label["key_citations"]
        assert example["outputs"]["required_tools"] == label["required_tools"]
        assert example["metadata"]["difficulty"] == label["difficulty"]
        assert example["metadata"]["category"] == label["category"]
        assert example["metadata"]["assessment_date"] == label["assessment_date"]


def test_metadata_difficulties_are_known():
    diffs = {e["metadata"]["difficulty"] for e in dataset.build_examples()}
    assert diffs == {"clean", "boundary", "failure", "adversarial"}


class FakeClient:
    """Minimal stand-in for langsmith.Client covering the upload flow."""

    def __init__(self, existing=False):
        self.existing = existing
        self.deleted = []
        self.created = []
        self.examples = None

    def has_dataset(self, dataset_name=None):
        return self.existing

    def delete_dataset(self, dataset_name=None):
        self.deleted.append(dataset_name)
        self.existing = False

    def create_dataset(self, name, description=None):
        self.created.append(name)

        class DataSet:
            id = "ds-123"

        return DataSet()

    def create_examples(self, dataset_id=None, examples=None, max_concurrency=1):
        self.examples = examples


def test_upload_frozen_when_exists():
    fake = FakeClient(existing=True)
    message = dataset.upload("windmill-test", client=fake)
    assert "already exists" in message
    assert fake.created == []
    assert fake.examples is None


def test_upload_force_replaces():
    fake = FakeClient(existing=True)
    message = dataset.upload("windmill-test", force=True, client=fake)
    assert fake.deleted == ["windmill-test"]
    assert fake.created == ["windmill-test"]
    assert fake.examples is not None
    assert len(fake.examples) == EXPECTED_CASES
    assert f"uploaded {EXPECTED_CASES} examples" in message


def test_upload_fresh():
    fake = FakeClient(existing=False)
    message = dataset.upload("windmill-test", client=fake)
    assert fake.deleted == []
    assert fake.created == ["windmill-test"]
    assert f"uploaded {EXPECTED_CASES}" in message
