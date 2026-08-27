"""
ForgeX — Tools Router

Endpoints for tool management and feasibility checks per spec §22.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.application.tool_service import ToolService

router = APIRouter(prefix="/api/tools", tags=["tools"])


class ToolCreate(BaseModel):
    name: str
    description: str
    tool_type: str  # http_request, webhook, composed_existing_tools
    is_sensitive: bool = False
    config: Optional[dict] = None
    input_schema: Optional[dict] = None


class ToolUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_sensitive: Optional[bool] = None
    config: Optional[dict] = None
    input_schema: Optional[dict] = None


class FeasibilityRequest(BaseModel):
    name: str
    description: Optional[str] = None
    tool_type: str
    config: Optional[dict] = None


@router.get("")
async def list_tools(session: AsyncSession = Depends(get_db_session)):
    service = ToolService(session)
    tools = await service.list_tools()
    return [
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "tool_type": t.tool_type,
            "is_builtin": t.is_builtin,
            "is_sensitive": t.is_sensitive,
            "input_schema": t.input_schema,
            "config": t.config if not t.is_builtin else None,
        }
        for t in tools
    ]


@router.post("/feasibility")
async def check_feasibility(
    body: FeasibilityRequest,
    session: AsyncSession = Depends(get_db_session),
):
    service = ToolService(session)
    return await service.check_feasibility(body.model_dump())


@router.post("")
async def create_tool(
    body: ToolCreate,
    session: AsyncSession = Depends(get_db_session),
):
    service = ToolService(session)
    # Run feasibility first
    check = await service.check_feasibility(body.model_dump())
    if not check["feasible"]:
        raise HTTPException(status_code=400, detail={"reasons": check["reasons"]})
    tool = await service.create_tool(body.model_dump())
    return {"id": tool.id, "name": tool.name, "created": True}


@router.patch("/{tool_id}")
async def update_tool(
    tool_id: str,
    body: ToolUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    service = ToolService(session)
    tool = await service.update_tool(tool_id, **body.model_dump(exclude_none=True))
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return {"id": tool.id, "name": tool.name, "updated": True}


@router.delete("/{tool_id}")
async def delete_tool(
    tool_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    service = ToolService(session)
    try:
        deleted = await service.delete_tool(tool_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not deleted:
        raise HTTPException(status_code=404, detail="Tool not found")
    return {"deleted": True}
