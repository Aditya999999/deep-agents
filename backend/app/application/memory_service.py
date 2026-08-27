"""
ForgeX — Memory Service

Multi-layer memory management per spec §7 + self-learning extension.

Memory Layers:
1. Working Memory  — Active conversation context (per-thread, ephemeral)
2. Episodic Memory — Key moments/interactions from past conversations (persistent)
3. Semantic Memory — Learned facts, preferences, domain knowledge (persistent)
4. AGENTS.md       — Structured memory file editable by user (per spec §7.2)
"""

import os
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path

from sqlalchemy import select, update, delete, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import (
    AgentMemoryVersion, EpisodicMemory, SemanticMemory
)
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("application.memory_service")


class MemoryService:
    """
    Multi-layer memory manager.

    Provides retrieval, storage, and context injection for all memory layers.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # ──────────────────────────────────────────────────────────────────────
    # AGENTS.md Memory (spec §7.2)
    # ──────────────────────────────────────────────────────────────────────

    async def get_agents_md(self, agent_config_id: str) -> dict:
        """Get the current AGENTS.md content for an agent."""
        stmt = (
            select(AgentMemoryVersion)
            .where(AgentMemoryVersion.agent_config_id == agent_config_id)
            .order_by(desc(AgentMemoryVersion.version))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        memory = result.scalar_one_or_none()

        if memory:
            return {
                "content": memory.content,
                "version": memory.version,
                "character_count": memory.character_count,
                "created_at": memory.created_at.isoformat() if memory.created_at else None,
            }
        return {"content": "", "version": 0, "character_count": 0}

    async def update_agents_md(self, agent_config_id: str, content: str) -> dict:
        """Save a new version of AGENTS.md content."""
        # Get current version
        current = await self.get_agents_md(agent_config_id)
        new_version = current.get("version", 0) + 1

        memory = AgentMemoryVersion(
            agent_config_id=agent_config_id,
            content=content,
            version=new_version,
            character_count=len(content),
        )
        self.session.add(memory)
        await self.session.flush()

        # Also write to filesystem for Deep Agents compatibility
        await self._write_agents_md_file(agent_config_id, content)

        logger.info(f"Updated AGENTS.md for agent {agent_config_id}, version {new_version}")
        return {
            "content": content,
            "version": new_version,
            "character_count": len(content),
        }

    async def _write_agents_md_file(self, agent_config_id: str, content: str) -> None:
        """Write AGENTS.md to filesystem for Deep Agents memory loading."""
        memory_dir = Path(settings.data_root) / "agents" / agent_config_id / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)
        memory_file = memory_dir / "AGENTS.md"
        memory_file.write_text(content, encoding="utf-8")

    # ──────────────────────────────────────────────────────────────────────
    # Episodic Memory
    # ──────────────────────────────────────────────────────────────────────

    async def store_episodic(
        self,
        agent_config_id: str,
        summary: str,
        context: Optional[str] = None,
        outcome: Optional[str] = None,
        importance: int = 5,
        tags: Optional[list[str]] = None,
        thread_id: Optional[str] = None,
    ) -> EpisodicMemory:
        """Store a new episodic memory."""
        memory = EpisodicMemory(
            agent_config_id=agent_config_id,
            thread_id=thread_id,
            summary=summary,
            context=context,
            outcome=outcome,
            importance=min(max(importance, 1), 10),
            tags=tags or [],
        )
        self.session.add(memory)
        await self.session.flush()
        logger.info(f"Stored episodic memory: {summary[:80]}")
        return memory

    async def get_episodic_memories(
        self,
        agent_config_id: str,
        limit: int = 20,
        min_importance: int = 1,
        tags: Optional[list[str]] = None,
    ) -> list[EpisodicMemory]:
        """Retrieve episodic memories, sorted by importance and recency."""
        stmt = (
            select(EpisodicMemory)
            .where(
                EpisodicMemory.agent_config_id == agent_config_id,
                EpisodicMemory.importance >= min_importance,
            )
            .order_by(desc(EpisodicMemory.importance), desc(EpisodicMemory.created_at))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        memories = list(result.scalars().all())

        # Filter by tags if specified
        if tags:
            memories = [
                m for m in memories
                if m.tags and any(t in m.tags for t in tags)
            ]

        return memories

    async def recall_episodic(self, memory_id: str) -> Optional[EpisodicMemory]:
        """Recall a specific episodic memory (increments access count)."""
        stmt = select(EpisodicMemory).where(EpisodicMemory.id == memory_id)
        result = await self.session.execute(stmt)
        memory = result.scalar_one_or_none()
        if memory:
            memory.access_count = (memory.access_count or 0) + 1
            memory.last_accessed = datetime.now(timezone.utc)
            await self.session.flush()
        return memory

    # ──────────────────────────────────────────────────────────────────────
    # Semantic Memory (Learned Knowledge)
    # ──────────────────────────────────────────────────────────────────────

    async def store_semantic(
        self,
        agent_config_id: str,
        category: str,
        key: str,
        value: str,
        confidence: int = 70,
        source: str = "inferred",
    ) -> SemanticMemory:
        """
        Store or reinforce a semantic memory.
        If a memory with the same key exists, it reinforces (updates confidence).
        """
        # Check for existing memory with same key
        stmt = select(SemanticMemory).where(
            SemanticMemory.agent_config_id == agent_config_id,
            SemanticMemory.key == key,
            SemanticMemory.is_active == True,
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Reinforce existing memory
            existing.reinforcement_count = (existing.reinforcement_count or 0) + 1
            existing.confidence = min(100, (existing.confidence or 50) + 5)
            existing.last_reinforced = datetime.now(timezone.utc)
            if value and value != existing.value:
                existing.value = value  # Update with newer information
            await self.session.flush()
            logger.info(f"Reinforced semantic memory: {key} (confidence: {existing.confidence})")
            return existing
        else:
            # Create new semantic memory
            memory = SemanticMemory(
                agent_config_id=agent_config_id,
                category=category,
                key=key,
                value=value,
                confidence=min(max(confidence, 0), 100),
                source=source,
            )
            self.session.add(memory)
            await self.session.flush()
            logger.info(f"Stored semantic memory: {key}")
            return memory

    async def get_semantic_memories(
        self,
        agent_config_id: str,
        category: Optional[str] = None,
        min_confidence: int = 0,
        limit: int = 50,
    ) -> list[SemanticMemory]:
        """Retrieve semantic memories filtered by category and confidence."""
        stmt = select(SemanticMemory).where(
            SemanticMemory.agent_config_id == agent_config_id,
            SemanticMemory.is_active == True,
            SemanticMemory.confidence >= min_confidence,
        )
        if category:
            stmt = stmt.where(SemanticMemory.category == category)
        stmt = stmt.order_by(desc(SemanticMemory.confidence), desc(SemanticMemory.updated_at)).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def deactivate_semantic(self, memory_id: str) -> bool:
        """Soft-delete a semantic memory."""
        stmt = (
            update(SemanticMemory)
            .where(SemanticMemory.id == memory_id)
            .values(is_active=False)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def delete_memory(self, memory_id: str, memory_type: str) -> bool:
        """Delete any type of memory by ID."""
        if memory_type == "episodic":
            stmt = delete(EpisodicMemory).where(EpisodicMemory.id == memory_id)
        elif memory_type == "semantic":
            stmt = delete(SemanticMemory).where(SemanticMemory.id == memory_id)
        else:
            return False
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    # ──────────────────────────────────────────────────────────────────────
    # Context Assembly (for agent injection)
    # ──────────────────────────────────────────────────────────────────────

    async def assemble_memory_context(self, agent_config_id: str) -> str:
        """
        Assemble all relevant memories into a context string
        for injection into the agent's system prompt.

        This is what makes the agent "remember" across conversations.
        """
        sections = []

        # 1. AGENTS.md content
        agents_md = await self.get_agents_md(agent_config_id)
        if agents_md.get("content"):
            sections.append(
                "## Persistent Memory (AGENTS.md)\n" + agents_md["content"]
            )

        # 2. High-confidence semantic memories
        semantic = await self.get_semantic_memories(
            agent_config_id, min_confidence=50, limit=30
        )
        if semantic:
            items = []
            for m in semantic:
                items.append(f"- **[{m.category}]** {m.key}: {m.value} (confidence: {m.confidence}%)")
            sections.append(
                "## Learned Knowledge\n" + "\n".join(items)
            )

        # 3. Recent important episodic memories
        episodic = await self.get_episodic_memories(
            agent_config_id, limit=10, min_importance=5
        )
        if episodic:
            items = []
            for m in episodic:
                items.append(f"- {m.summary}")
                if m.outcome:
                    items.append(f"  → Outcome: {m.outcome}")
            sections.append(
                "## Key Past Interactions\n" + "\n".join(items)
            )

        if not sections:
            return ""

        return (
            "\n\n---\n"
            "# Agent Memory Context\n"
            "The following is your accumulated memory from past interactions. "
            "Use this to provide personalized, context-aware responses.\n\n"
            + "\n\n".join(sections)
        )

    async def get_memory_stats(self, agent_config_id: str) -> dict:
        """Get memory statistics for an agent."""
        ep_count = await self.session.execute(
            select(func.count(EpisodicMemory.id)).where(
                EpisodicMemory.agent_config_id == agent_config_id
            )
        )
        sem_count = await self.session.execute(
            select(func.count(SemanticMemory.id)).where(
                SemanticMemory.agent_config_id == agent_config_id,
                SemanticMemory.is_active == True,
            )
        )
        agents_md = await self.get_agents_md(agent_config_id)

        return {
            "episodic_count": ep_count.scalar() or 0,
            "semantic_count": sem_count.scalar() or 0,
            "agents_md_version": agents_md.get("version", 0),
            "agents_md_characters": agents_md.get("character_count", 0),
        }
