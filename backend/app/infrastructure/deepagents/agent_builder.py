"""
ForgeX — Agent Builder

Uses deepagents.create_deep_agent to build compiled LangGraph Deep Agents per spec §6.1.
Coordinates model binding (AzureClaudeChat), tools, skills, memory, planning, and backend.
"""

from typing import Any, Dict, List, Optional
from deepagents import create_deep_agent
from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import settings
from app.core.logging import get_logger
from app.infrastructure.deepagents.skill_loader import SkillLoader
from app.tools import get_tools_by_names
from azure_claude_chat import AzureClaudeChat

logger = get_logger("deepagents.agent_builder")


class AgentBuilder:
    """Constructs compiled Deep Agents using deepagents.create_deep_agent."""

    def __init__(self):
        self.skill_loader = SkillLoader()

    def build_agent(self, config_dict: Dict[str, Any]):
        """
        Translates stored config into create_deep_agent parameter structure
        and returns the compiled LangGraph agent graph.
        """
        agent_id = config_dict.get("id", "default")
        name = config_dict.get("name", "ForgeX Agent")
        system_prompt = config_dict.get("system_prompt", "You are ForgeX, a self-learning Deep Agent.")
        debug_mode = config_dict.get("debug_mode", False)

        # 1. Model binding — AzureClaudeChat instance
        model = AzureClaudeChat(
            api_key=settings.azure_claude_api_key,
            base_url=settings.azure_claude_base_url,
            model=settings.azure_claude_model,
        )

        # 2. Enabled Tools
        tool_names = [
            t.get("tool_name") or t.get("name")
            for t in config_dict.get("tools", [])
            if t.get("enabled", True)
        ]
        tools = get_tools_by_names(tool_names) if tool_names else []

        # 3. Discovered Skills
        skills = self.skill_loader.discover_skills(agent_id)
        skill_paths = [s["path"] for s in skills] if skills else None

        logger.info(
            f"Calling create_deep_agent for '{name}' (id={agent_id}, "
            f"tools={len(tools)}, skills={len(skill_paths or [])})"
        )

        try:
            compiled_graph = create_deep_agent(
                model=model,
                tools=tools if tools else None,
                system_prompt=system_prompt,
                skills=skill_paths,
                debug=debug_mode,
                name=name,
            )
            return compiled_graph
        except Exception as e:
            logger.warning(f"create_deep_agent initialization warning: {e}. Returning definition dictionary.")
            return {
                "name": name,
                "model": model,
                "tools": tools,
                "system_prompt": system_prompt,
                "skills": skills,
            }
