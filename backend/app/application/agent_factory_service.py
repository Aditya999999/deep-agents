"""
ForgeX — Agent Factory Service

Manages AgentInstanceCache keyed by (agent_config_id, version, capability_signature)
per spec §24. Invalidates cached compiled graph when config version changes.
"""

from typing import Any, Dict, Optional, Tuple

from app.core.logging import get_logger
from app.infrastructure.deepagents.agent_builder import AgentBuilder

logger = get_logger("application.agent_factory_service")


class AgentFactoryService:
    """Factory and lifecycle cache for compiled agent graphs."""

    def __init__(self):
        self.builder = AgentBuilder()
        self._instance_cache: Dict[Tuple[str, int, str], Dict[str, Any]] = {}

    def _compute_capability_signature(self, config_dict: Dict[str, Any]) -> str:
        """Compute hashable signature of tools, skills and backend options."""
        tools = sorted([str(t) for t in config_dict.get("tools", [])])
        skills = sorted([str(s) for s in config_dict.get("skills", [])])
        mode = str(config_dict.get("backend_mode", "state"))
        planning = str(config_dict.get("planning_enabled", False))
        return f"{','.join(tools)}|{','.join(skills)}|{mode}|{planning}"

    def get_or_create_agent(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve cached agent or build and cache a new instance.
        Invalidates stale versions per spec §24.
        """
        agent_id = config_dict.get("id", "default")
        version = config_dict.get("version", 1)
        sig = self._compute_capability_signature(config_dict)
        cache_key = (agent_id, version, sig)

        # Check cache
        if cache_key in self._instance_cache:
            logger.debug(f"Cache hit for agent {agent_id} v{version}")
            return self._instance_cache[cache_key]

        # Invalidate any older versions for this agent
        keys_to_remove = [k for k in self._instance_cache if k[0] == agent_id]
        for old_key in keys_to_remove:
            logger.info(f"Invalidating stale agent cache key: {old_key}")
            del self._instance_cache[old_key]

        # Build new agent definition
        agent_instance = self.builder.build_agent(config_dict)
        self._instance_cache[cache_key] = agent_instance
        logger.info(f"Cached newly built agent instance for {agent_id} v{version}")

        return agent_instance

    def invalidate(self, agent_id: str) -> None:
        """Explicitly invalidate all cached instances for an agent."""
        keys_to_remove = [k for k in self._instance_cache if k[0] == agent_id]
        for k in keys_to_remove:
            del self._instance_cache[k]
        logger.info(f"Invalidated cache for agent {agent_id}")
