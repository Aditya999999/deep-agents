"""
ForgeX — Thread Repository

CRUD for conversation threads and messages.
"""

from typing import Optional
from sqlalchemy import select, delete, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.db.models import Thread, ThreadMessage


class ThreadRepository:
    """Repository for thread persistence."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> Thread:
        thread = Thread(**kwargs)
        self.session.add(thread)
        await self.session.flush()
        return thread

    async def get_by_id(self, thread_id: str) -> Optional[Thread]:
        stmt = (
            select(Thread)
            .options(selectinload(Thread.messages))
            .where(Thread.id == thread_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, limit: int = 50) -> list[Thread]:
        stmt = (
            select(Thread)
            .where(Thread.status == "active")
            .order_by(Thread.updated_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_title(self, thread_id: str, title: str) -> Optional[Thread]:
        thread = await self.get_by_id(thread_id)
        if thread:
            thread.title = title
            await self.session.flush()
        return thread

    async def delete_by_id(self, thread_id: str) -> bool:
        stmt = delete(Thread).where(Thread.id == thread_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def add_message(self, thread_id: str, **kwargs) -> ThreadMessage:
        # Get next sequence number
        stmt = select(func.coalesce(func.max(ThreadMessage.seq), 0)).where(
            ThreadMessage.thread_id == thread_id
        )
        result = await self.session.execute(stmt)
        next_seq = result.scalar() + 1

        msg = ThreadMessage(thread_id=thread_id, seq=next_seq, **kwargs)
        self.session.add(msg)

        # Update thread message count
        stmt2 = (
            update(Thread)
            .where(Thread.id == thread_id)
            .values(message_count=next_seq)
        )
        await self.session.execute(stmt2)
        await self.session.flush()
        return msg

    async def get_messages(self, thread_id: str) -> list[ThreadMessage]:
        stmt = (
            select(ThreadMessage)
            .where(ThreadMessage.thread_id == thread_id)
            .order_by(ThreadMessage.seq)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
