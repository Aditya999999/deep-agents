"""
ForgeX — Built-in Tools Registry

All tools are built with the @tool decorator from langchain_core.tools,
making them directly compatible with create_deep_agent(tools=[...]).

Usage:
    from app.tools import ALL_TOOLS, get_tool_by_name

    agent = create_deep_agent(model=model, tools=ALL_TOOLS)
"""

from app.tools.calculator import calculator
from app.tools.web_search import web_search
from app.tools.http_fetch import http_fetch
from app.tools.document_inspector import document_inspector

# All built-in tools as LangChain tool instances
ALL_TOOLS = [calculator, web_search, http_fetch, document_inspector]

# Name → tool mapping for selective enablement
TOOL_MAP = {t.name: t for t in ALL_TOOLS}


def get_tool_by_name(name: str):
    """Get a built-in tool by name. Returns None if not found."""
    return TOOL_MAP.get(name)


def get_tools_by_names(names: list[str]) -> list:
    """Get multiple tools by name, filtering out any not found."""
    return [TOOL_MAP[n] for n in names if n in TOOL_MAP]
