"""P0 scaffold smoke test: pins resolve, project packages import, layout present."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_runtime_imports():
    import fastmcp  # noqa: F401
    import langchain  # noqa: F401
    import langchain.mcp  # noqa: F401
    import langchain_openai  # noqa: F401
    import langsmith  # noqa: F401


def test_project_packages_import():
    import evals  # noqa: F401
    import src  # noqa: F401
    import src.mcp_server  # noqa: F401
    import src.tools  # noqa: F401


def test_layout():
    for rel in [
        ".env.example",
        "requirements.txt",
        "knowledge/policy",
        "cases/fixtures",
        "cases/labels",
        "evals/results",
    ]:
        assert (ROOT / rel).exists(), f"missing: {rel}"
