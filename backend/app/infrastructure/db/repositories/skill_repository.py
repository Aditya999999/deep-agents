"""
ForgeX — Skill Repository

CRUD for skill metadata.
"""

from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import Skill


class SkillRepository:
    """Repository for skill persistence."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> Skill:
        skill = Skill(**kwargs)
        self.session.add(skill)
        await self.session.flush()
        return skill

    async def get_by_id(self, skill_id: str) -> Optional[Skill]:
        stmt = select(Skill).where(Skill.id == skill_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Skill]:
        stmt = select(Skill).order_by(Skill.name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_by_id(self, skill_id: str, **kwargs) -> Optional[Skill]:
        skill = await self.get_by_id(skill_id)
        if not skill:
            return None
        for key, value in kwargs.items():
            if hasattr(skill, key):
                setattr(skill, key, value)
        await self.session.flush()
        return skill

    async def delete_by_id(self, skill_id: str) -> bool:
        stmt = delete(Skill).where(Skill.id == skill_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0
