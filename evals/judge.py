"""LLM judge for dossier groundedness - the protocol's only model-based signal.

The judge receives exactly what the agent received (the case-service evidence block),
the text of the policy sections the dossier cites, and the dossier itself. It answers:
does every check's rule application follow from the cited policy text and the evidence,
and are all figures supported? Output is a compact structured verdict.

No temperature is set (the GPT-6 family rejects explicit temperature - same as the agent).

Calibration lives in evals/calibration.py: the user labels a sample of judged items
independently, and agreement is computed against their labels.
"""

import json

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from src import config
from src.mcp_server.case_service import get_case_files
from src.tools.search_policy import load_policy_sections


class JudgeVerdict(BaseModel):
    """Structured judge output for one dossier."""

    grounded: bool = Field(
        description=(
            "True when every check's rule application follows from the cited policy text "
            "and the evidence."
        )
    )
    score: int = Field(
        ge=1,
        le=5,
        description=(
            "Groundedness 1-5: 1 = fabricated reasoning or invented rules; 3 = mostly "
            "grounded with some unsupported claims; 5 = every claim supported."
        ),
    )
    unsupported_claims: list[str] = Field(
        description=(
            "Specific claims or figures the cited policy text and evidence do not support; "
            "empty when none."
        )
    )
    comment: str = Field(description="Short justification, 2-4 sentences.")


JUDGE_SYSTEM_PROMPT = (
    "You are a strict mortgage-underwriting reviewer grading an automated pre-assessment "
    "dossier for groundedness. You receive the case evidence, the text of the policy "
    "sections the dossier cites, and the dossier. For every check, verify that the stated "
    "rule application follows from the cited policy text and from the evidence, and that "
    "all figures match the evidence. Flag invented rules, misapplied thresholds, and "
    "unsupported numbers or claims. Do not introduce outside policy knowledge; judge only "
    "against the policy text provided. Then return the structured verdict."
)


def load_cited_sections(citations: list[str]) -> str:
    """Text of the cited policy sections; unknown ids are marked, not fatal."""
    sections = {
        doc.metadata["section_id"]: f"{doc.metadata['title']}\n\n{doc.page_content}"
        for doc in load_policy_sections()
    }
    blocks = []
    for section_id in sorted(set(citations)):
        text = sections.get(section_id, "(no such section in the policy corpus)")
        blocks.append(f"### {section_id}\n{text}")
    return "\n\n".join(blocks)


def build_judge_messages(case_id: str, dossier: dict) -> list[dict]:
    """The judge prompt: evidence, cited sections, dossier - nothing else."""
    citations = [
        citation
        for check in dossier.get("checks", [])
        for citation in check.get("citations") or []
    ]
    user = (
        f"CASE EVIDENCE ({case_id}) - exactly what the agent received:\n\n"
        f"{get_case_files(case_id)}\n\n"
        f"CITED POLICY SECTIONS:\n\n{load_cited_sections(citations)}\n\n"
        f"SUBMITTED DOSSIER (JSON):\n\n{json.dumps(dossier, indent=2)}\n\n"
        "Grade the dossier's groundedness now."
    )
    return [
        {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def make_judge(model: str | None = None):
    """Structured-output judge runnable (lazy: no network until invoked)."""
    llm = ChatOpenAI(model=model or config.JUDGE_MODEL)
    return llm.with_structured_output(JudgeVerdict)


async def judge_case(
    case_id: str, dossier: dict, *, model: str | None = None
) -> JudgeVerdict:
    result = await make_judge(model).ainvoke(build_judge_messages(case_id, dossier))
    return JudgeVerdict.model_validate(result)
