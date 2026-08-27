"""
ForgeX — Tool Repository

CRUD for tool definitions.
"""

from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import ToolDefinition


class ToolRepository:
    """Repository for tool definition persistence."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> ToolDefinition:
        tool = ToolDefinition(**kwargs)
        self.session.add(tool)
        await self.session.flush()
        return tool

    async def get_by_id(self, tool_id: str) -> Optional[ToolDefinition]:
        stmt = select(ToolDefinition).where(ToolDefinition.id == tool_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[ToolDefinition]:
        stmt = select(ToolDefinition).where(ToolDefinition.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> list[ToolDefinition]:
        stmt = select(ToolDefinition).order_by(ToolDefinition.name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_builtin(self) -> list[ToolDefinition]:
        stmt = select(ToolDefinition).where(ToolDefinition.is_builtin == True).order_by(ToolDefinition.name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_by_id(self, tool_id: str, **kwargs) -> Optional[ToolDefinition]:
        tool = await self.get_by_id(tool_id)
        if not tool:
            return None
        for key, value in kwargs.items():
            if hasattr(tool, key):
                setattr(tool, key, value)
        await self.session.flush()
        return tool

    async def delete_by_id(self, tool_id: str) -> bool:
        stmt = delete(ToolDefinition).where(ToolDefinition.id == tool_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0
