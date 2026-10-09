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

CASE_SERVICE_SERVER = Path(__file__).resolve().parents[1] / "mcp_server" / "case_service.py"
REQUIRED_TOOLS = ("get_case_files", "submit_dossier")


def case_service_transport(server_path: Path | None = None) -> PythonStdioTransport:
    """Stdio transport for the case-service: this interpreter, current environment."""
    return PythonStdioTransport(
        script_path=server_path or CASE_SERVICE_SERVER,
        python_cmd=sys.executable,
        env={**os.environ},
    )


async def get_case_service_tools(server_path: Path | None = None) -> list[BaseTool]:
    """Discover the case-service MCP tools as LangChain tools."""
    adapter = MCPAdapter(case_service_transport(server_path))
    tools = await adapter.list_tools()
    names = {t.name for t in tools}
    missing = [name for name in REQUIRED_TOOLS if name not in names]
    if missing:
        raise RuntimeError(
            f"case-service is missing expected tools {missing}; server exposed {sorted(names)}"
        )
    return tools
