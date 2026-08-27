"""
ForgeX — Memory & Learning Router

Endpoints for AGENTS.md memory, episodic/semantic memories,
user feedback, and learning log per spec §22 + self-learning extension.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.application.memory_service import MemoryService
from app.application.learning_service import LearningService

router = APIRouter(tags=["memories"])


# ── DTOs ───────────────────────────────────────────────────────────────────

class MemoryUpdate(BaseModel):
    content: str


class FeedbackSubmit(BaseModel):
    message_id: str
    rating: str  # positive, negative
    correction: Optional[str] = None
    original_response: Optional[str] = None
    agent_config_id: Optional[str] = None


# ── AGENTS.md Routes ───────────────────────────────────────────────────────

@router.get("/api/agent-configs/{config_id}/memory")
async def get_memory(
    config_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    service = MemoryService(session)
    return await service.get_agents_md(config_id)


@router.put("/api/agent-configs/{config_id}/memory")
async def update_memory(
    config_id: str,
    body: MemoryUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    service = MemoryService(session)
    return await service.update_agents_md(config_id, body.content)


# ── Episodic Memory Routes ────────────────────────────────────────────────

@router.get("/api/agent-configs/{config_id}/memories/episodic")
async def list_episodic_memories(
    config_id: str,
    limit: int = 20,
    min_importance: int = 1,
    session: AsyncSession = Depends(get_db_session),
):
    service = MemoryService(session)
    memories = await service.get_episodic_memories(config_id, limit=limit, min_importance=min_importance)
    return [
        {
            "id": m.id,
            "summary": m.summary,
            "context": m.context,
            "outcome": m.outcome,
            "importance": m.importance,
            "tags": m.tags,
            "access_count": m.access_count,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in memories
    ]


# ── Semantic Memory Routes ────────────────────────────────────────────────

@router.get("/api/agent-configs/{config_id}/memories/semantic")
async def list_semantic_memories(
    config_id: str,
    category: Optional[str] = None,
    min_confidence: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_db_session),
):
    service = MemoryService(session)
    memories = await service.get_semantic_memories(
        config_id, category=category, min_confidence=min_confidence, limit=limit
    )
    return [
        {
            "id": m.id,
            "category": m.category,
            "key": m.key,
            "value": m.value,
            "confidence": m.confidence,
            "source": m.source,
            "reinforcement_count": m.reinforcement_count,
            "is_active": m.is_active,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "updated_at": m.updated_at.isoformat() if m.updated_at else None,
        }
        for m in memories
    ]


# ── Memory Stats ──────────────────────────────────────────────────────────

@router.get("/api/agent-configs/{config_id}/memories/stats")
async def get_memory_stats(
    config_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    service = MemoryService(session)
    return await service.get_memory_stats(config_id)


# ── Delete Memory ─────────────────────────────────────────────────────────

@router.delete("/api/memories/{memory_id}")
async def delete_memory(
    memory_id: str,
    memory_type: str = "episodic",
    session: AsyncSession = Depends(get_db_session),
):
    service = MemoryService(session)
    deleted = await service.delete_memory(memory_id, memory_type)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"deleted": True}


# ── Feedback & Learning Routes ────────────────────────────────────────────

@router.post("/api/threads/{thread_id}/feedback")
async def submit_feedback(
    thread_id: str,
    body: FeedbackSubmit,
    session: AsyncSession = Depends(get_db_session),
):
    service = LearningService(session)
    feedback = await service.submit_feedback(
        thread_id=thread_id,
        message_id=body.message_id,
        rating=body.rating,
        correction=body.correction,
        original_response=body.original_response,
        agent_config_id=body.agent_config_id,
    )
    return {
        "id": feedback.id,
        "rating": feedback.rating,
        "processed": feedback.processed,
    }


@router.get("/api/agent-configs/{config_id}/learning-log")
async def get_learning_log(
    config_id: str,
    limit: int = 30,
    session: AsyncSession = Depends(get_db_session),
):
    service = LearningService(session)
    events = await service.get_learning_log(config_id, limit=limit)
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "description": e.description,
            "memories_created": e.memories_created,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]


@router.get("/api/agent-configs/{config_id}/learning-stats")
async def get_learning_stats(
    config_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    service = LearningService(session)
    return await service.get_learning_stats(config_id)
