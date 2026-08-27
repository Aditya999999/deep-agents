"""
ForgeX — Agent Configuration Router

CRUD endpoints for agent configurations per spec §22.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.infrastructure.db.repositories.agent_config_repository import AgentConfigRepository

router = APIRouter(prefix="/api/agent-configs", tags=["agent-configs"])


# ── Pydantic DTOs ──────────────────────────────────────────────────────────

class AgentConfigCreate(BaseModel):
    name: str = "ForgeX Agent"
    system_prompt: str = "You are ForgeX, a helpful AI agent with self-learning capabilities. You remember past interactions and learn from feedback."
    planning_enabled: bool = False
    response_format: str = "plain_text"
    response_schema: Optional[dict] = None
    backend_mode: str = "state"
    debug_mode: bool = False
    interrupt_policy: Optional[dict] = None
    permissions: Optional[dict] = None


class AgentConfigUpdate(BaseModel):
    name: Optional[str] = None
    system_prompt: Optional[str] = None
    planning_enabled: Optional[bool] = None
    response_format: Optional[str] = None
    response_schema: Optional[dict] = None
    backend_mode: Optional[str] = None
    debug_mode: Optional[bool] = None
    interrupt_policy: Optional[dict] = None
    permissions: Optional[dict] = None


class AgentToolsUpdate(BaseModel):
    tools: list[dict]  # [{tool_definition_id, require_approval, enabled}]


class AgentSkillsUpdate(BaseModel):
    skill_ids: list[str]


# ── Routes ─────────────────────────────────────────────────────────────────

@router.post("")
async def create_agent_config(
    body: AgentConfigCreate,
    session: AsyncSession = Depends(get_db_session),
):
    repo = AgentConfigRepository(session)
    config = await repo.create(**body.model_dump(exclude_none=True))
    return _serialize_config(config)


@router.get("")
async def list_agent_configs(
    session: AsyncSession = Depends(get_db_session),
):
    repo = AgentConfigRepository(session)
    configs = await repo.list_all()
    return [_serialize_config_summary(c) for c in configs]


@router.get("/{config_id}")
async def get_agent_config(
    config_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    repo = AgentConfigRepository(session)
    config = await repo.get_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Agent configuration not found")
    return _serialize_config(config)


@router.patch("/{config_id}")
async def update_agent_config(
    config_id: str,
    body: AgentConfigUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    repo = AgentConfigRepository(session)
    config = await repo.update_by_id(config_id, **body.model_dump(exclude_none=True))
    if not config:
        raise HTTPException(status_code=404, detail="Agent configuration not found")
    return _serialize_config(config)


@router.delete("/{config_id}")
async def delete_agent_config(
    config_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    repo = AgentConfigRepository(session)
    deleted = await repo.delete_by_id(config_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Agent configuration not found")
    return {"deleted": True}


@router.put("/{config_id}/tools")
async def set_agent_tools(
    config_id: str,
    body: AgentToolsUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    repo = AgentConfigRepository(session)
    config = await repo.get_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Agent configuration not found")
    await repo.set_tools(config_id, body.tools)
    return {"updated": True}


@router.put("/{config_id}/skills")
async def set_agent_skills(
    config_id: str,
    body: AgentSkillsUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    repo = AgentConfigRepository(session)
    config = await repo.get_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Agent configuration not found")
    await repo.set_skills(config_id, body.skill_ids)
    return {"updated": True}


# ── Serializers ────────────────────────────────────────────────────────────

def _serialize_config(config) -> dict:
    return {
        "id": config.id,
        "name": config.name,
        "system_prompt": config.system_prompt,
        "planning_enabled": config.planning_enabled,
        "response_format": config.response_format,
        "response_schema": config.response_schema,
        "backend_mode": config.backend_mode,
        "debug_mode": config.debug_mode,
        "interrupt_policy": config.interrupt_policy,
        "permissions": config.permissions,
        "version": config.version,
        "is_active": config.is_active,
        "created_at": config.created_at.isoformat() if config.created_at else None,
        "updated_at": config.updated_at.isoformat() if config.updated_at else None,
        "tools": [
            {
                "id": at.id,
                "tool_definition_id": at.tool_definition_id,
                "tool_name": at.tool_definition.name if at.tool_definition else None,
                "tool_description": at.tool_definition.description if at.tool_definition else None,
                "require_approval": at.require_approval,
                "enabled": at.enabled,
            }
            for at in (config.agent_tools or [])
        ],
        "skills": [
            {
                "id": ask.id,
                "skill_id": ask.skill_id,
                "skill_name": ask.skill.name if ask.skill else None,
                "enabled": ask.enabled,
            }
            for ask in (config.agent_skills or [])
        ],
        "subagents": [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "system_prompt": s.system_prompt,
                "enabled": s.enabled,
            }
            for s in (config.subagents or [])
        ],
    }


def _serialize_config_summary(config) -> dict:
    return {
        "id": config.id,
        "name": config.name,
        "version": config.version,
        "is_active": config.is_active,
        "planning_enabled": config.planning_enabled,
        "created_at": config.created_at.isoformat() if config.created_at else None,
        "updated_at": config.updated_at.isoformat() if config.updated_at else None,
    }
