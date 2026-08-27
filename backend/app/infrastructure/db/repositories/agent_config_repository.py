"""
ForgeX — Agent Configuration Repository

CRUD operations for AgentConfig entities.
Uses interface pattern per spec §5.1 (Dependency Inversion).
"""

from typing import Optional
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.db.models import (
    AgentConfig, AgentTool, ToolDefinition, AgentSkill, Skill, SubagentConfig
)


class AgentConfigRepository:
    """Repository for agent configuration persistence."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> AgentConfig:
        config = AgentConfig(**kwargs)
        self.session.add(config)
        await self.session.flush()
        loaded = await self.get_by_id(config.id)
        return loaded or config

    async def get_by_id(self, config_id: str) -> Optional[AgentConfig]:
        stmt = (
            select(AgentConfig)
            .options(
                selectinload(AgentConfig.agent_tools).selectinload(AgentTool.tool_definition),
                selectinload(AgentConfig.agent_skills).selectinload(AgentSkill.skill),
                selectinload(AgentConfig.subagents),
            )
            .where(AgentConfig.id == config_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> list[AgentConfig]:
        stmt = select(AgentConfig).order_by(AgentConfig.updated_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_by_id(self, config_id: str, **kwargs) -> Optional[AgentConfig]:
        # Increment version on update
        config = await self.get_by_id(config_id)
        if not config:
            return None
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        config.version = (config.version or 0) + 1
        await self.session.flush()
        return config

    async def delete_by_id(self, config_id: str) -> bool:
        stmt = delete(AgentConfig).where(AgentConfig.id == config_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def set_tools(self, config_id: str, tool_ids: list[dict]) -> None:
        """Replace agent tools. tool_ids is list of {tool_definition_id, require_approval, enabled}."""
        # Delete existing
        stmt = delete(AgentTool).where(AgentTool.agent_config_id == config_id)
        await self.session.execute(stmt)
        # Add new
        for t in tool_ids:
            agent_tool = AgentTool(
                agent_config_id=config_id,
                tool_definition_id=t["tool_definition_id"],
                require_approval=t.get("require_approval", False),
                enabled=t.get("enabled", True),
            )
            self.session.add(agent_tool)
        await self.session.flush()

    async def set_skills(self, config_id: str, skill_ids: list[str]) -> None:
        """Replace agent skills."""
        stmt = delete(AgentSkill).where(AgentSkill.agent_config_id == config_id)
        await self.session.execute(stmt)
        for sid in skill_ids:
            agent_skill = AgentSkill(
                agent_config_id=config_id,
                skill_id=sid,
                enabled=True,
            )
            self.session.add(agent_skill)
        await self.session.flush()
