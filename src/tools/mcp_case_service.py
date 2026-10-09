"""The single place that knows how the MCP case-service is wired.

Everything transport-related for the case-service lives here: the adapter
(langchain.mcp MCPAdapter), the server path and the subprocess environment. The rest
of the codebase just asks for LangChain tools by name, so a transport/adapter change
(or the in-process fallback) only touches this module.

Two deliberate choices:
- The MCP SDK spawns stdio servers with a small whitelisted environment by default
  (`get_default_environment`), so the current environment is passed through explicitly:
  the server reads its WINDMILL_* overrides (run id, fixtures/submissions directories)
  from it. Without this, submissions would silently land in the wrong run's folder.
- `python_cmd` is pinned to the current interpreter so the server always runs in the
  project virtualenv, whatever launched the agent.

Each returned tool opens its own connection per call; FastMCP keeps the server
subprocess alive between calls (keep_alive defaults to True).
"""

import os
import sys
from pathlib import Path

from fastmcp.client.transports import PythonStdioTransport
from langchain_core.tools import BaseTool
from langchain.mcp import MCPAdapter
from pydantic import BaseModel, Field

from src.schemas import Dossier

CASE_SERVICE_SERVER = Path(__file__).resolve().parents[1] / "mcp_server" / "case_service.py"
REQUIRED_TOOLS = ("get_case_files", "submit_dossier")


class GetCaseFilesArgs(BaseModel):
    """Arguments for get_case_files."""

    case_id: str = Field(description="The case id, e.g. 'case-001'.")


class SubmitDossierArgs(BaseModel):
    """Arguments for submit_dossier: the case id and the complete dossier."""

    case_id: str = Field(description="The case id, e.g. 'case-001'.")
    dossier: Dossier = Field(description="The complete assessment dossier to submit.")


ARG_MODELS: dict[str, type[BaseModel]] = {
    "get_case_files": GetCaseFilesArgs,
    "submit_dossier": SubmitDossierArgs,
}


def case_service_transport(server_path: Path | None = None) -> PythonStdioTransport:
    """Stdio transport for the case-service: this interpreter, current environment."""
    return PythonStdioTransport(
        script_path=server_path or CASE_SERVICE_SERVER,
        python_cmd=sys.executable,
        env={**os.environ},
    )


async def get_case_service_tools(server_path: Path | None = None) -> list[BaseTool]:
    """Discover the case-service MCP tools as LangChain tools.

    Each tool's argument schema is replaced with an explicit Pydantic model. Reason:
    create_agent binds OpenAI-compatible tools with strict=True, and under strict the
    converter degrades an open `dict[str, Any]` argument to a property-less closed
    object - the dossier parameter became unusable and the API rejected the tool.
    With the full Dossier structure nested in the schema, the strict conversion is
    valid and the model receives the dossier's entire shape inside the tool call.
    """
    adapter = MCPAdapter(case_service_transport(server_path))
    tools = await adapter.list_tools()
    names = {t.name for t in tools}
    missing = [name for name in REQUIRED_TOOLS if name not in names]
    if missing:
        raise RuntimeError(
            f"case-service is missing expected tools {missing}; server exposed {sorted(names)}"
        )
    for tool in tools:
        if tool.name in ARG_MODELS:
            tool.args_schema = ARG_MODELS[tool.name]
    return tools
