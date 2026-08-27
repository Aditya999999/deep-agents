"""
ForgeX — Tool Service

Tool registry, feasibility checks, and runtime tool creation per spec §10.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.repositories.tool_repository import ToolRepository
from app.infrastructure.db.models import ToolDefinition
from app.core.logging import get_logger

logger = get_logger("application.tool_service")

# Allowed runtime tool types per spec §10
ALLOWED_RUNTIME_TYPES = {"http_request", "webhook", "composed_existing_tools"}

# Built-in tool definitions
BUILTIN_TOOLS = [
    {
        "name": "calculator",
        "description": "Safe mathematical expression evaluator. Supports arithmetic, trigonometry, logarithms.",
        "tool_type": "builtin",
        "is_builtin": True,
        "is_sensitive": False,
        "input_schema": {
            "type": "object",
            "properties": {"expression": {"type": "string", "description": "Mathematical expression to evaluate"}},
            "required": ["expression"],
        },
    },
    {
        "name": "web_search",
        "description": "Search the public web and return structured results with titles, URLs, and snippets.",
        "tool_type": "builtin",
        "is_builtin": True,
        "is_sensitive": False,
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Max results", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "http_fetch",
        "description": "Retrieve and normalize a public web page. Includes SSRF protection and size limits.",
        "tool_type": "builtin",
        "is_builtin": True,
        "is_sensitive": True,
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string", "description": "URL to fetch"}},
            "required": ["url"],
        },
    },
    {
        "name": "document_inspector",
        "description": "Inspect uploaded documents — extract text, metadata, and file information.",
        "tool_type": "builtin",
        "is_builtin": True,
        "is_sensitive": False,
        "input_schema": {
            "type": "object",
            "properties": {"file_path": {"type": "string", "description": "Path to the document file"}},
            "required": ["file_path"],
        },
    },
]


class ToolService:
    """Application service for tool management."""

    def __init__(self, session: AsyncSession):
        self.repo = ToolRepository(session)
        self.session = session

    async def ensure_builtin_tools(self) -> None:
        """Create built-in tool definitions if they don't exist."""
        for tool_def in BUILTIN_TOOLS:
            existing = await self.repo.get_by_name(tool_def["name"])
            if not existing:
                await self.repo.create(**tool_def)
                logger.info(f"Created built-in tool: {tool_def['name']}")

    async def list_tools(self) -> list[ToolDefinition]:
        return await self.repo.list_all()

    async def get_tool(self, tool_id: str) -> Optional[ToolDefinition]:
        return await self.repo.get_by_id(tool_id)

    async def check_feasibility(self, tool_data: dict) -> dict:
        """
        Check if a runtime tool definition is feasible per spec §10.

        Returns:
            dict with feasible (bool), reasons (list), and warnings (list)
        """
        reasons = []
        warnings = []

        tool_type = tool_data.get("tool_type", "")
        name = tool_data.get("name", "")

        # Type check
        if tool_type not in ALLOWED_RUNTIME_TYPES:
            reasons.append(f"Tool type '{tool_type}' is not allowed. Allowed types: {', '.join(ALLOWED_RUNTIME_TYPES)}")

        # Name collision check
        if name:
            existing = await self.repo.get_by_name(name)
            if existing:
                reasons.append(f"A tool with name '{name}' already exists")

        # Name validation
        if not name or len(name) < 2:
            reasons.append("Tool name must be at least 2 characters")
        elif len(name) > 100:
            reasons.append("Tool name must be 100 characters or fewer")

        # Description check
        if not tool_data.get("description"):
            warnings.append("A description is recommended for better agent understanding")

        # HTTP request specific validations
        if tool_type == "http_request":
            config = tool_data.get("config", {})
            url = config.get("url", "")
            if url:
                from app.tools.http_fetch import _validate_url
                valid, reason = _validate_url(url)
                if not valid:
                    reasons.append(f"URL validation failed: {reason}")

        feasible = len(reasons) == 0
        return {
            "feasible": feasible,
            "reasons": reasons,
            "warnings": warnings,
        }

    async def create_tool(self, tool_data: dict) -> ToolDefinition:
        """Create a new runtime tool definition."""
        return await self.repo.create(**tool_data)

    async def update_tool(self, tool_id: str, **kwargs) -> Optional[ToolDefinition]:
        return await self.repo.update_by_id(tool_id, **kwargs)

    async def delete_tool(self, tool_id: str) -> bool:
        # Don't allow deleting built-in tools
        tool = await self.repo.get_by_id(tool_id)
        if tool and tool.is_builtin:
            raise ValueError("Cannot delete built-in tools")
        return await self.repo.delete_by_id(tool_id)
