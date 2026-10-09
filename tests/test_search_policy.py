"""Tests for policy retrieval: corpus parsing (offline) and retrieval quality (online).

The retrieval tests call the OpenAI embedding API and are skipped when no key is set;
everything else is offline.
"""

import os
import re

import pytest

from src import config  # noqa: F401  (loads .env so the key check below is accurate)
from src.tools import search_policy

SECTION_ID_RE = re.compile(r"^POL-[A-Z]+-\d{2}$")
HAS_KEY = bool(os.environ.get("OPENAI_API_KEY"))

EXPECTED_HITS = [
    ("stress rate floor for affordability", "POL-AFF-01"),
    ("how recent must the employer letter be", "POL-DOC-02"),
    ("satisfied CCJ within how many months is a problem", "POL-CREDIT-01"),
    ("self-employed minimum years of tax evidence", "POL-SE-01"),
    ("maximum loan to value", "POL-LTV-01"),
    ("what happens when documents are missing versus exceptions", "POL-STAT-01"),
    ("age at the end of the mortgage term", "POL-AGE-01"),
    ("evidenced annual income from payslips", "POL-INC-01"),
    ("declared versus evidenced income variance tolerance", "POL-INC-02"),
    ("high LTV expert sign-off bands", "POL-LTV-01"),
]


def test_loader_parses_every_section():
    docs = search_policy.load_policy_sections()
    assert len(docs) == 12
    ids = [d.metadata["section_id"] for d in docs]
    assert len(set(ids)) == 12
    for doc in docs:
        assert SECTION_ID_RE.match(doc.metadata["section_id"])
        assert doc.metadata["title"]
        assert doc.page_content.startswith(f"# {doc.metadata['section_id']}")


def test_tool_is_named_and_typed():
    assert search_policy.search_policy.name == "search_policy"
    schema = search_policy.search_policy.get_input_schema().model_json_schema()
    assert "query" in schema["properties"]


@pytest.mark.skipif(not HAS_KEY, reason="OPENAI_API_KEY not set; retrieval tests need embeddings")
@pytest.mark.parametrize("query,expected_id", EXPECTED_HITS)
def test_retrieval_finds_expected_section(query, expected_id):
    result = search_policy.search_policy.invoke({"query": query})
    assert f"### {expected_id} -" in result
