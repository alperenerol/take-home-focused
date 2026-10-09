"""Agent assembly: a single ReAct agent (create_agent over LangGraph) with four tools.

Native tools: search_policy (policy RAG) and mortgage_calculator (deterministic math).
MCP tools: get_case_files and submit_dossier, discovered through the case-service
wiring module. The dossier schema drives the agent's structured final response.
"""

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from src import config
from src.prompt import SYSTEM_PROMPT
from src.schemas import Dossier
from src.tools.calculator import mortgage_calculator
from src.tools.mcp_case_service import get_case_service_tools
from src.tools.search_policy import search_policy


async def build_agent():
    """Build the assessment agent; discovers case-service tools over MCP."""
    # The Luna-class model rejects explicit temperature settings (only the default is
    # supported), so it is left unset.
    model = ChatOpenAI(model=config.AGENT_MODEL)
    case_tools = await get_case_service_tools()
    tools = [search_policy, mortgage_calculator, *case_tools]
    return create_agent(
        model,
        tools,
        system_prompt=SYSTEM_PROMPT,
        response_format=Dossier,
        name="windmill-assessor",
    )
