"""Tests for policy retrieval: corpus parsing (offline) and retrieval quality (needs embeddings).

The retrieval tests call the OpenAI embedding API and are skipped when no key is set;
`make test-retrieval` sets REQUIRE_EMBEDDINGS=1 so they *fail* instead of skipping.

Probe provenance (see evals/reports/retrieval-probes.md):
  - CURATED: hand-written probes, kept from the first version of this suite.
  - TRACE: verbatim `search_policy` query strings the agent produced in the v1 and v2 runs,
    extracted from the LangSmith tool runs (216 + 255 calls, 433 distinct strings).

Every probe carries `max_rank`: the rank its expected section(s) reached when the ceiling was
recorded. `test_retrieval_rank_ceiling` fails if a section drops below its recorded rank, so a
regression in ranking is visible instead of being absorbed by a top-3 membership check. A
failure here means ranking moved - investigate before touching the number.
"""

import os
import re

import pytest

from src import config  # noqa: F401  (loads .env so the key check below is accurate)
from src.tools import search_policy

SECTION_ID_RE = re.compile(r"^POL-[A-Z]+-\d{2}$")
HAS_KEY = bool(os.environ.get("OPENAI_API_KEY"))
REQUIRE_EMBEDDINGS = os.environ.get("REQUIRE_EMBEDDINGS") == "1"

needs_embeddings = pytest.mark.skipif(
    not HAS_KEY and not REQUIRE_EMBEDDINGS,
    reason="no OPENAI_API_KEY; retrieval probes need embeddings (run `make test-retrieval` to require them)",
)

# (query, expected section ids, highest rank the expected section(s) may reach, note)
Probe = tuple[str, tuple[str, ...], int, str]

CURATED_PROBES: list[Probe] = [
    ("stress rate floor for affordability", ("POL-AFF-01",), 1, ""),
    ("how recent must the employer letter be", ("POL-DOC-02",), 1, ""),
    ("satisfied CCJ within how many months is a problem", ("POL-CREDIT-01",), 1, ""),
    ("self-employed minimum years of tax evidence", ("POL-SE-01",), 1, ""),
    ("maximum loan to value", ("POL-LTV-01",), 1, ""),
    ("what happens when documents are missing versus exceptions", ("POL-STAT-01",), 1, ""),
    ("age at the end of the mortgage term", ("POL-AGE-01",), 1, ""),
    ("evidenced annual income from payslips", ("POL-INC-01",), 1, ""),
    ("declared versus evidenced income variance tolerance", ("POL-INC-02",), 1, ""),
    ("high LTV expert sign-off bands", ("POL-LTV-01",), 1, ""),
    ("what does this pre-assessment actually cover and which principles apply", ("POL-GEN-01",), 1, ""),
    ("does an exception get looked at by a human", ("POL-EXC-01",), 1, ""),
    (
        "employer letter says one salary, payslips say another - what then",
        ("POL-EXC-01",),
        4,
        "known near-miss: a contradiction phrased in income vocabulary ranks the income and "
        "self-employment sections above POL-EXC-01, so at k=3 the contradiction rule is not "
        "returned. Recorded, not hidden; see the finding in evals/reports/retrieval-probes.md.",
    ),
]

TRACE_PROBES: list[Probe] = [
    (
        "required documents for employed mortgage applicant declaration, identity, payslips, "
        "employer letter, credit report and exact missing item tokens",
        ("POL-DOC-01",),
        1,
        "",
    ),
    (
        "material contradiction between employer letter salary and payslip-implied annual income "
        "refer expert manual review",
        ("POL-EXC-01",),
        3,
        "same near-miss family as the curated contradiction probe: reaches the section at rank 3",
    ),
    (
        "expert manual review status when exception flagged and required actions referral rules",
        ("POL-EXC-01", "POL-STAT-01"),
        2,
        "multi-topic query: names the referral rule (EXC) and the status rule (STAT)",
    ),
    (
        "dossier status check ids outcomes missing documents exceptions manual review POL-STAT-01",
        ("POL-STAT-01",),
        1,
        "real queries sometimes name the section id outright",
    ),
    (
        "DTI and stressed affordability limits monthly commitments mortgage payment stressed rate "
        "LTV above 85",
        ("POL-AFF-01", "POL-LTV-01"),
        2,
        "multi-topic query: affordability and the LTV band that triggers the stressed rate",
    ),
    ("loan to value bands maximum LTV and handling when exceeded", ("POL-LTV-01",), 1, ""),
    ("credit report satisfied CCJ and default registered marker treatment", ("POL-CREDIT-01",), 1, ""),
    (
        "employed income evidence required number of payslips and employer letter income calculation",
        ("POL-INC-01",),
        1,
        "",
    ),
    ("declared annual income versus evidenced income variance tolerance 5 percent", ("POL-INC-02",), 1, ""),
    ("maximum age at mortgage term end years and days convention referral", ("POL-AGE-01",), 1, ""),
    (
        "self-employed income evidence SA302 and tax year overview branches by years trading",
        ("POL-SE-01",),
        1,
        "",
    ),
    (
        "self-employed evidence SA302 tax year overviews, fewer than three tax years business "
        "history branches",
        ("POL-SE-01",),
        1,
        "",
    ),
    (
        "recency window for dated mortgage evidence documents payslips employer letter credit report",
        ("POL-DOC-02",),
        1,
        "",
    ),
    ("dated evidence document recency window at assessment date", ("POL-DOC-02",), 1, ""),
    (
        "required documents and missing item tokens for self-employed mortgage case, identity and "
        "credit report",
        ("POL-DOC-01",),
        1,
        "",
    ),
]

PROBES: list[Probe] = CURATED_PROBES + TRACE_PROBES

# Off-domain queries the corpus should not be answering. The tool has no abstention path - it
# always returns k sections - and these probes record why: on the current corpus and embedding
# model the similarity bands *overlap*. Measured top-1: off-domain max 0.380 (an ombudsman-
# complaints question, which shares real vocabulary with a bank corpus), on-topic min 0.311 (a
# colloquially-worded question about a rule the corpus states formally). 1 of 28 on-topic probes
# scores below the worst off-domain query, so no threshold on this score can abstain. The load
# sits in the prompt rule "cite only what retrieval returned" and in the dossier-level citation
# evaluators, not in the similarity score.
OFF_DOMAIN_QUERIES = [
    "how do I reset my online banking password",
    "what is the interest rate for a five year fixed mortgage product",
    "complaints handling procedure and how to escalate to the financial ombudsman",
    "office opening hours and branch address for Manchester",
]

# Aggregate floors, deliberately below the recorded values (recall@3 0.967, MRR 0.941) so that
# genuine degradation fails while small embedding drift does not.
RECALL_AT_3_FLOOR = 0.95
MRR_FLOOR = 0.88


def ranked_sections(query: str, k: int = 6) -> list[tuple[str, float]]:
    """(section_id, similarity) for the top k sections; similarity is higher-is-better."""
    hits = search_policy.get_store().similarity_search_with_score(query, k=k)
    return [(doc.metadata["section_id"], score) for doc, score in hits]


def rank_of(section_id: str, ranked: list[tuple[str, float]]) -> int | None:
    """1-based rank of a section, or None if it is outside the ranked window."""
    return next((i + 1 for i, (sid, _) in enumerate(ranked) if sid == section_id), None)


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


def test_probe_set_covers_every_policy_section():
    """Offline: no retrievable section may go unprobed (coverage was 9 of 12 before hardening)."""
    corpus_ids = {doc.metadata["section_id"] for doc in search_policy.load_policy_sections()}
    probed = {section_id for _, expected, _, _ in PROBES for section_id in expected}
    assert probed == corpus_ids, f"unprobed sections: {sorted(corpus_ids - probed)}"


@needs_embeddings
@pytest.mark.parametrize(
    "query,expected,max_rank,note",
    PROBES,
    ids=[f"{'/'.join(e)}-{q[:40]}" for q, e, _, _ in PROBES],
)
def test_retrieval_rank_ceiling(query, expected, max_rank, note):
    ranked = ranked_sections(query)
    ranks = {section_id: rank_of(section_id, ranked) for section_id in expected}
    for section_id, rank in ranks.items():
        assert rank is not None, f"{section_id} not in top 6 for {query!r}\nranked: {ranked}\n{note}"
        assert rank <= max_rank, (
            f"{section_id} dropped to rank {rank} (ceiling {max_rank}) for {query!r}\n"
            f"ranked: {ranked}\n{note}"
        )


@needs_embeddings
def test_tool_output_carries_section_ids():
    """The agent can only cite what the tool text spells out, so the heading format is a contract."""
    result = search_policy.search_policy.invoke({"query": "maximum age at mortgage term end", "k": 2})
    ranked = ranked_sections("maximum age at mortgage term end", k=2)
    assert len(ranked) == 2
    for section_id, _ in ranked:
        assert f"### {section_id} -" in result


@needs_embeddings
def test_retrieval_recall_at_3_and_mrr():
    """Aggregate view: recall@3 over all expected sections, MRR over the best expected per probe."""
    found = total = 0
    reciprocal = []
    for query, expected, _, _ in PROBES:
        ranked = ranked_sections(query, k=3)
        best = None
        for section_id in expected:
            rank = rank_of(section_id, ranked)
            total += 1
            if rank is not None:
                found += 1
                best = rank if best is None else min(best, rank)
        reciprocal.append(1.0 / best if best else 0.0)

    recall = found / total
    mrr = sum(reciprocal) / len(reciprocal)
    assert recall >= RECALL_AT_3_FLOOR, f"recall@3 {recall:.3f} < {RECALL_AT_3_FLOOR} ({found}/{total})"
    assert mrr >= MRR_FLOOR, f"MRR {mrr:.3f} < {MRR_FLOOR}"


@needs_embeddings
def test_similarity_bands_overlap_so_no_score_threshold_abstains():
    """Documents the finding that blocks a score-threshold guard.

    If this fails because the bands have separated, do not delete the test: update the finding in
    evals/reports/retrieval-probes.md and the README retrieval section, then decide whether an
    abstention threshold is now worth adding.
    """
    off_tops = {q: ranked_sections(q, k=1)[0][1] for q in OFF_DOMAIN_QUERIES}
    on_tops = {q: ranked_sections(q, k=1)[0][1] for q, _, _, _ in PROBES}

    worst_off = max(off_tops.items(), key=lambda item: item[1])
    best_on = min(on_tops.items(), key=lambda item: item[1])
    assert worst_off[1] >= best_on[1], (
        f"similarity bands now separate (worst off-domain {worst_off[1]:.3f} < best on-topic "
        f"{best_on[1]:.3f}); update the documented finding before changing this test.\n"
        f"  worst off-domain: {worst_off[0]!r}\n  best on-topic: {best_on[0]!r}"
    )


@pytest.mark.skipif(not REQUIRE_EMBEDDINGS, reason="only enforced by `make test-retrieval`")
def test_embedding_key_is_present_when_required():
    assert HAS_KEY, "REQUIRE_EMBEDDINGS=1 but OPENAI_API_KEY is unset: retrieval would be untested"
