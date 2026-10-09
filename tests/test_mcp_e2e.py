"""End-to-end test: the case-service over real MCP stdio through the wiring module.

Uses src/tools/mcp_case_service.get_case_service_tools - the same path the agent
takes - to list tools, read a case and submit a dossier, then checks the stored
artifact. The WINDMILL_* overrides set in this test must reach the server subprocess:
that environment pass-through is part of what this test proves.
"""

import asyncio
import json

from src.tools.mcp_case_service import get_case_service_tools

DOSSIER = {
    "case_id": "case-001",
    "status": "READY_FOR_UNDERWRITING",
    "checks": [
        {
            "check_id": "CHK-LTV",
            "outcome": "PASSED",
            "rationale": "LTV 68.75 is band A.",
            "citations": ["POL-LTV-01"],
            "missing_items": [],
        }
    ],
    "required_actions": [],
    "summary": "Assessed; ready for underwriting.",
}


def _extract_text(result) -> str:
    content = result[0] if isinstance(result, tuple) else result
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                parts.append(block.get("text", ""))
            else:
                parts.append(getattr(block, "text", str(block)))
        return "".join(parts)
    return str(content)


async def _run_e2e():
    tools = await get_case_service_tools()
    by_name = {t.name: t for t in tools}
    assert sorted(by_name) == ["get_case_files", "submit_dossier"]

    res = await by_name["get_case_files"].ainvoke({"case_id": "case-001"})
    payload = json.loads(_extract_text(res))
    assert payload["case_id"] == "case-001"
    assert payload["declaration"]["loan"]["amount_gbp"] == 220000
    assert payload["evidence_file_count"] == 6

    res = await by_name["submit_dossier"].ainvoke({"case_id": "case-001", "dossier": DOSSIER})
    assert "accepted" in _extract_text(res)


def test_case_service_over_stdio(tmp_path, monkeypatch):
    monkeypatch.setenv("WINDMILL_SUBMITTED_DIR", str(tmp_path))
    monkeypatch.setenv("WINDMILL_RUN_ID", "pytest-e2e")
    asyncio.run(_run_e2e())
    stored = json.loads((tmp_path / "pytest-e2e" / "case-001.json").read_text())
    assert stored["dossier"]["case_id"] == "case-001"
    assert stored["run_id"] == "pytest-e2e"
