"""
ForgeX — Agent Builder

Translates persisted AgentConfig entities into runnable execution units per spec §6.1.
Coordinates model binding (AzureClaudeChat), tools, skills, memory paths, and middleware.
"""

from typing import Any, Dict, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import settings
from app.core.logging import get_logger
from app.infrastructure.deepagents.backend_factory import BackendFactory
from app.infrastructure.deepagents.checkpoint_factory import CheckpointFactory
from app.infrastructure.deepagents.skill_loader import SkillLoader
from app.tools import get_tools_by_names
from azure_claude_chat import AzureClaudeChat

logger = get_logger("deepagents.agent_builder")


class AgentBuilder:
    """Constructs configured Deep Agent definitions."""

    def __init__(self):
        self.skill_loader = SkillLoader()
        self.checkpoint_factory = CheckpointFactory()

    def build_agent(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translates stored config into create_deep_agent parameter structure.
        """
        agent_id = config_dict.get("id", "default")
        name = config_dict.get("name", "ForgeX Agent")
        system_prompt = config_dict.get("system_prompt", "You are ForgeX, a helpful Deep Agent.")
        backend_mode = config_dict.get("backend_mode", "state")
        planning_enabled = config_dict.get("planning_enabled", False)

        # 1. Model binding — reuse AzureClaudeChat instance
        model = AzureClaudeChat(
            api_key=settings.azure_claude_api_key,
            base_url=settings.azure_claude_base_url,
            model=settings.azure_claude_model,
        )

        # 2. Tools
        tool_names = [
            t.get("tool_name") or t.get("name")
            for t in config_dict.get("tools", [])
            if t.get("enabled", True)
        ]
        tools = get_tools_by_names(tool_names) if tool_names else []

        # 3. Skills
        skills = self.skill_loader.discover_skills(agent_id)

        # 4. Backend
        backend = BackendFactory.create_backend(mode=backend_mode)

        # 5. Checkpointer
        checkpoint_path = self.checkpoint_factory.get_checkpoint_db_path()

        logger.info(f"Built agent definition for '{name}' (id={agent_id}, tools={len(tools)}, skills={len(skills)})")

        return {
            "name": name,
            "model": model,
            "tools": tools,
            "system_prompt": system_prompt,
            "skills": skills,
            "backend": backend,
            "planning_enabled": planning_enabled,
            "checkpoint_db_path": checkpoint_path,
            "interrupt_policy": config_dict.get("interrupt_policy", {}),
            "response_format": config_dict.get("response_format", "plain_text"),
        }
