"""
ForgeX — API Dependencies

FastAPI dependency injection wiring per spec §5.1 (Dependency Inversion).
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.sqlite import async_session_factory
from app.infrastructure.db.repositories.agent_config_repository import AgentConfigRepository
from app.infrastructure.db.repositories.tool_repository import ToolRepository
from app.infrastructure.db.repositories.thread_repository import ThreadRepository
from app.infrastructure.db.repositories.skill_repository import SkillRepository
from app.application.agent_service import AgentService
from app.application.tool_service import ToolService
from app.application.memory_service import MemoryService
from app.application.learning_service import LearningService


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_agent_config_repo(session: AsyncSession) -> AgentConfigRepository:
    return AgentConfigRepository(session)


async def get_tool_repo(session: AsyncSession) -> ToolRepository:
    return ToolRepository(session)


async def get_thread_repo(session: AsyncSession) -> ThreadRepository:
    return ThreadRepository(session)


async def get_skill_repo(session: AsyncSession) -> SkillRepository:
    return SkillRepository(session)


def get_agent_service() -> AgentService:
    return AgentService()


async def get_tool_service(session: AsyncSession) -> ToolService:
    return ToolService(session)


async def get_memory_service(session: AsyncSession) -> MemoryService:
    return MemoryService(session)


async def get_learning_service(session: AsyncSession) -> LearningService:
    return LearningService(session)
