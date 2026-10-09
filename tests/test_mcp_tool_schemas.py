"""Regression: case-service tool schemas must survive strict-mode conversion.

create_agent binds OpenAI-compatible tools with strict=True; an open `dict[str, Any]`
argument is degraded by the strict converter to a property-less closed object, which
made the submit_dossier tool unusable (and was rejected by the API). These checks pin
the fixed shape: full dossier structure nested in the schema, required == all
properties, additionalProperties False at every level.
"""

import asyncio
import json

from langchain_core.utils.function_calling import convert_to_openai_tool

from src.tools.mcp_case_service import get_case_service_tools


def _strict_params(tool):
    conv = convert_to_openai_tool(tool, strict=True)["function"]
    assert conv.get("strict") is True
    return conv["parameters"]


def test_case_service_tools_strict_safe(tmp_path, monkeypatch):
    monkeypatch.setenv("WINDMILL_SUBMITTED_DIR", str(tmp_path))

    async def _run():
        tools = await get_case_service_tools()
        return {t.name: _strict_params(t) for t in tools}

    params = asyncio.run(_run())

    for name, p in params.items():
        assert p.get("additionalProperties") is False, f"{name}: root must be closed"
        assert sorted(p.get("required", [])) == sorted(p["properties"].keys()), (
            f"{name}: strict requires every property in required"
        )

    dossier = params["submit_dossier"]["properties"]["dossier"]
    assert dossier["additionalProperties"] is False
    assert sorted(dossier["required"]) == [
        "case_id",
        "checks",
        "required_actions",
        "status",
        "summary",
    ]
    checks_items = dossier["properties"]["checks"]["items"]
    assert checks_items.get("additionalProperties") is False
    for field in ("check_id", "outcome", "rationale", "citations", "missing_items"):
        assert field in checks_items["properties"]
    blob = json.dumps(dossier)
    for member in ("READY_FOR_UNDERWRITING", "EXCEPTION_FLAGGED", "CHK-AFFORDABILITY"):
        assert member in blob
