"""Policy retrieval for the mortgage assessment agent.

Per-section chunking: every POL-*.md section in knowledge/policy is one chunk, so a
retrieval result maps 1:1 to a policy section id and citations can be trusted. The
corpus is small, so the index is an in-memory vector store (no external infrastructure)
built lazily on first use and cached for the process lifetime.
"""

from functools import lru_cache
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.tools import tool
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings

from src import config


def load_policy_sections(knowledge_dir: Path | None = None) -> list[Document]:
    """Parse knowledge/policy/POL-*.md into one Document per section (sorted by id)."""
    directory = Path(knowledge_dir or config.KNOWLEDGE_DIR)
    docs: list[Document] = []
    for path in sorted(directory.glob("POL-*.md")):
        text = path.read_text(encoding="utf-8")
        first_line = text.splitlines()[0] if text else ""
        title = first_line.split(" - ", 1)[1] if " - " in first_line else first_line.lstrip("# ")
        docs.append(
            Document(
                page_content=text,
                metadata={"section_id": path.stem, "title": title, "source": path.name},
            )
        )
    return docs


@lru_cache(maxsize=1)
def get_store() -> InMemoryVectorStore:
    """Build (once) the in-memory vector store over the policy corpus."""
    store = InMemoryVectorStore(OpenAIEmbeddings(model=config.EMBEDDING_MODEL))
    store.add_documents(load_policy_sections())
    return store


@tool
def search_policy(query: str, k: int = 3) -> str:
    """Search the Windmill Bank underwriting policy corpus and return the most relevant
    policy sections with their section ids. Use it before applying any rule: quote and
    cite the section ids (e.g. POL-AFF-01) that the rule comes from. Search with a
    focused description of the rule you need (one rule or topic per call), for example
    "document recency window for payslips" or "stressed affordability limit above 85
    percent LTV".

    Args:
        query: What to look up in the policy corpus.
        k: Number of sections to return (1-6, default 3).

    Returns:
        Up to k policy sections, each headed by its section id and title.
    """
    k = max(1, min(int(k), 6))
    hits = get_store().similarity_search(query, k=k)
    parts = []
    for doc in hits:
        parts.append(
            f"### {doc.metadata['section_id']} - {doc.metadata['title']}\n\n{doc.page_content}"
        )
    return "\n\n---\n\n".join(parts)
