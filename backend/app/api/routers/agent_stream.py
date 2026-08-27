"""
ForgeX — Agent Streaming Router

Endpoints for the Agent Streaming Protocol per spec §16 and §22.
POST /api/threads/{thread_id}/commands
GET  /api/threads/{thread_id}/stream
GET  /api/threads/{thread_id}/state
GET  /api/threads/{thread_id}/history
"""

import json
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.application.agent_service import AgentService
from app.application.memory_service import MemoryService
from app.application.learning_service import LearningService
from app.infrastructure.db.repositories.thread_repository import ThreadRepository
from app.infrastructure.db.repositories.agent_config_repository import AgentConfigRepository
from app.infrastructure.streaming.agent_server_protocol import protocol_adapter

router = APIRouter(prefix="/api/threads", tags=["agent-stream"])

# Singleton agent service
_agent_service = AgentService()


class CommandRequest(BaseModel):
    command: str = "run"  # run, resume, cancel
    input: Optional[list[dict]] = None  # [{role: "human", content: "..."}]
    message: Optional[str] = None
    agent_config_id: Optional[str] = None
    run_id: Optional[str] = None


class ThreadCreate(BaseModel):
    agent_config_id: Optional[str] = None
    title: Optional[str] = None


class ThreadUpdate(BaseModel):
    title: Optional[str] = None


# ── Thread Management ─────────────────────────────────────────────────────

@router.post("")
async def create_thread(
    body: ThreadCreate,
    session: AsyncSession = Depends(get_db_session),
):
    repo = ThreadRepository(session)
    thread = await repo.create(
        agent_config_id=body.agent_config_id,
        title=body.title or "New Conversation",
    )
    return {"id": thread.id, "title": thread.title, "created_at": thread.created_at.isoformat()}


@router.get("")
async def list_threads(
    limit: int = 50,
    session: AsyncSession = Depends(get_db_session),
):
    repo = ThreadRepository(session)
    threads = await repo.list_all(limit=limit)
    return [
        {
            "id": t.id,
            "title": t.title,
            "agent_config_id": t.agent_config_id,
            "status": t.status,
            "message_count": t.message_count,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        }
        for t in threads
    ]


@router.patch("/{thread_id}")
async def update_thread(
    thread_id: str,
    body: ThreadUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    repo = ThreadRepository(session)
    if body.title:
        thread = await repo.update_title(thread_id, body.title)
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
    return {"updated": True}


@router.delete("/{thread_id}")
async def delete_thread(
    thread_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    repo = ThreadRepository(session)
    deleted = await repo.delete_by_id(thread_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Thread not found")
    return {"deleted": True}


# ── Agent Streaming Protocol ──────────────────────────────────────────────

@router.post("/{thread_id}/commands")
async def submit_command(
    thread_id: str,
    body: CommandRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """Submit a command to the agent (run, resume, cancel)."""
    repo = ThreadRepository(session)
    thread = await repo.get_by_id(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    if body.command == "cancel" and body.run_id:
        _agent_service.cancel_run(body.run_id)
        return {"cancelled": True}

    # Build the command payload
    command = {}
    if body.input:
        command["input"] = body.input
    elif body.message:
        command["input"] = [{"role": "human", "content": body.message}]

    # Get agent config for memory context injection
    agent_config = None
    config_id = body.agent_config_id or thread.agent_config_id
    if config_id:
        config_repo = AgentConfigRepository(session)
        db_config = await config_repo.get_by_id(config_id)
        if db_config:
            agent_config = {
                "name": db_config.name,
                "system_prompt": db_config.system_prompt,
                "planning_enabled": db_config.planning_enabled,
            }

            # Inject memory context into system prompt
            memory_service = MemoryService(session)
            memory_context = await memory_service.assemble_memory_context(config_id)
            if memory_context:
                agent_config["system_prompt"] = (
                    db_config.system_prompt + "\n\n" + memory_context
                )

    # Store user message
    user_content = ""
    if body.input:
        for msg in body.input:
            if msg.get("role") == "human":
                user_content = msg.get("content", "")
    elif body.message:
        user_content = body.message

    if user_content:
        await repo.add_message(
            thread_id=thread_id,
            role="user",
            content=user_content,
        )

    # Execute the command
    run_id = await _agent_service.execute_command(thread_id, command, agent_config)

    # Trigger learning from the user message (async extraction)
    if config_id and user_content:
        learning_service = LearningService(session)
        await learning_service.extract_insights_from_thread(
            agent_config_id=config_id,
            thread_id=thread_id,
            messages=[{"role": "user", "content": user_content}],
        )

    return {"run_id": run_id, "thread_id": thread_id}


@router.get("/{thread_id}/stream")
async def stream_events(
    thread_id: str,
    run_id: Optional[str] = Query(None),
    from_seq: int = Query(0),
):
    """SSE stream of agent events per spec §16.4."""
    if not run_id:
        raise HTTPException(status_code=400, detail="run_id is required")

    async def event_generator():
        async for event in _agent_service.stream_events(run_id, from_seq=from_seq):
            # Record in protocol adapter for replay
            protocol_adapter.record_event(run_id, event)
            # Format as SSE
            yield protocol_adapter.format_sse_event(event)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{thread_id}/state")
async def get_thread_state(
    thread_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Get the current state of a thread."""
    repo = ThreadRepository(session)
    thread = await repo.get_by_id(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    return {
        "thread_id": thread.id,
        "title": thread.title,
        "status": thread.status,
        "message_count": thread.message_count,
    }


@router.get("/{thread_id}/history")
async def get_thread_history(
    thread_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Get the message history for a thread."""
    repo = ThreadRepository(session)
    messages = await repo.get_messages(thread_id)
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "tool_calls": m.tool_calls,
            "tool_call_id": m.tool_call_id,
            "metadata": m.metadata_,
            "seq": m.seq,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in messages
    ]
