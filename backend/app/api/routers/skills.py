"""
ForgeX — Skills Router

Endpoints for skill management per spec §22.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.infrastructure.db.repositories.skill_repository import SkillRepository

router = APIRouter(prefix="/api/skills", tags=["skills"])


class SkillCreate(BaseModel):
    name: str
    description: Optional[str] = None
    directory_name: str
    skill_md_content: Optional[str] = None
    frontmatter: Optional[dict] = None


class SkillUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    skill_md_content: Optional[str] = None
    frontmatter: Optional[dict] = None


@router.get("")
async def list_skills(session: AsyncSession = Depends(get_db_session)):
    repo = SkillRepository(session)
    skills = await repo.list_all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "directory_name": s.directory_name,
            "frontmatter": s.frontmatter,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in skills
    ]


@router.post("")
async def create_skill(
    body: SkillCreate,
    session: AsyncSession = Depends(get_db_session),
):
    repo = SkillRepository(session)
    skill = await repo.create(**body.model_dump(exclude_none=True))
    return {"id": skill.id, "name": skill.name, "created": True}


@router.patch("/{skill_id}")
async def update_skill(
    skill_id: str,
    body: SkillUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    repo = SkillRepository(session)
    skill = await repo.update_by_id(skill_id, **body.model_dump(exclude_none=True))
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"id": skill.id, "name": skill.name, "updated": True}


@router.delete("/{skill_id}")
async def delete_skill(
    skill_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    repo = SkillRepository(session)
    deleted = await repo.delete_by_id(skill_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"deleted": True}
