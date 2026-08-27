"""
ForgeX Deep Agent Platform — Database ORM Models

SQLAlchemy models for all persistent entities per spec §8.2.
Tables: agent_configs, tool_definitions, agent_tools, skills,
        agent_skills, threads, agent_memory_versions.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text, JSON
)
from sqlalchemy.orm import relationship

from app.infrastructure.db.sqlite import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


class AgentConfig(Base):
    """Agent configuration — the core entity users create and edit."""
    __tablename__ = "agent_configs"

    id = Column(String, primary_key=True, default=_new_id)
    name = Column(String(255), nullable=False, default="ForgeX Agent")
    system_prompt = Column(Text, nullable=False, default="You are ForgeX, a helpful AI agent.")
    planning_enabled = Column(Boolean, default=False)
    response_format = Column(String(50), default="plain_text")
    response_schema = Column(JSON, nullable=True)
    backend_mode = Column(String(50), default="state")
    debug_mode = Column(Boolean, default=False)
    interrupt_policy = Column(JSON, nullable=True, default=dict)
    permissions = Column(JSON, nullable=True, default=dict)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    # Relationships
    agent_tools = relationship("AgentTool", back_populates="agent_config", cascade="all, delete-orphan", lazy="selectin")
    agent_skills = relationship("AgentSkill", back_populates="agent_config", cascade="all, delete-orphan", lazy="selectin")
    subagents = relationship("SubagentConfig", back_populates="agent_config", cascade="all, delete-orphan", lazy="selectin")


class ToolDefinition(Base):
    """Tool definitions — both built-in and user-created."""
    __tablename__ = "tool_definitions"

    id = Column(String, primary_key=True, default=_new_id)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=False)
    tool_type = Column(String(50), nullable=False)  # builtin, http_request, webhook, composed
    is_builtin = Column(Boolean, default=False)
    is_sensitive = Column(Boolean, default=False)
    config = Column(JSON, nullable=True)
    input_schema = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class AgentTool(Base):
    """Many-to-many: which tools are enabled for which agent."""
    __tablename__ = "agent_tools"

    id = Column(String, primary_key=True, default=_new_id)
    agent_config_id = Column(String, ForeignKey("agent_configs.id", ondelete="CASCADE"), nullable=False)
    tool_definition_id = Column(String, ForeignKey("tool_definitions.id", ondelete="CASCADE"), nullable=False)
    require_approval = Column(Boolean, default=False)
    enabled = Column(Boolean, default=True)

    agent_config = relationship("AgentConfig", back_populates="agent_tools", lazy="selectin")
    tool_definition = relationship("ToolDefinition", lazy="selectin")


class Skill(Base):
    """Skill metadata — directories with SKILL.md."""
    __tablename__ = "skills"

    id = Column(String, primary_key=True, default=_new_id)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    directory_name = Column(String(255), nullable=False)
    skill_md_content = Column(Text, nullable=True)
    frontmatter = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class AgentSkill(Base):
    """Many-to-many: which skills are enabled for which agent."""
    __tablename__ = "agent_skills"

    id = Column(String, primary_key=True, default=_new_id)
    agent_config_id = Column(String, ForeignKey("agent_configs.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(String, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    enabled = Column(Boolean, default=True)

    agent_config = relationship("AgentConfig", back_populates="agent_skills", lazy="selectin")
    skill = relationship("Skill", lazy="selectin")


class AgentMemoryVersion(Base):
    """Versioned AGENTS.md content for an agent."""
    __tablename__ = "agent_memory_versions"

    id = Column(String, primary_key=True, default=_new_id)
    agent_config_id = Column(String, ForeignKey("agent_configs.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False, default="")
    version = Column(Integer, default=1)
    character_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utcnow)


class Thread(Base):
    """Conversation threads."""
    __tablename__ = "threads"

    id = Column(String, primary_key=True, default=_new_id)
    agent_config_id = Column(String, ForeignKey("agent_configs.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(500), nullable=True, default="New Conversation")
    status = Column(String(50), default="active")  # active, archived
    message_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    # Store messages as JSON for simplicity in v1
    messages = relationship("ThreadMessage", back_populates="thread", cascade="all, delete-orphan",
                            order_by="ThreadMessage.seq", lazy="selectin")


class ThreadMessage(Base):
    """Individual messages within a thread."""
    __tablename__ = "thread_messages"

    id = Column(String, primary_key=True, default=_new_id)
    thread_id = Column(String, ForeignKey("threads.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)  # user, assistant, tool, system
    content = Column(Text, nullable=False, default="")
    tool_calls = Column(JSON, nullable=True)
    tool_call_id = Column(String, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    seq = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=_utcnow)

    thread = relationship("Thread", back_populates="messages")


class SubagentConfig(Base):
    """Configured subagents for an agent."""
    __tablename__ = "subagent_configs"

    id = Column(String, primary_key=True, default=_new_id)
    agent_config_id = Column(String, ForeignKey("agent_configs.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=True)
    tools = Column(JSON, nullable=True)
    skills = Column(JSON, nullable=True)
    permissions = Column(JSON, nullable=True)
    interrupt_policy = Column(JSON, nullable=True)
    response_format = Column(String(50), nullable=True)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)

    agent_config = relationship("AgentConfig", back_populates="subagents")


# ─── Self-Learning & Memory System ────────────────────────────────────────────


class EpisodicMemory(Base):
    """
    Episodic memories — key moments/outcomes from past conversations.
    These are specific interaction records the agent can reference.
    """
    __tablename__ = "episodic_memories"

    id = Column(String, primary_key=True, default=_new_id)
    agent_config_id = Column(String, ForeignKey("agent_configs.id", ondelete="CASCADE"), nullable=False)
    thread_id = Column(String, ForeignKey("threads.id", ondelete="SET NULL"), nullable=True)
    summary = Column(Text, nullable=False)
    context = Column(Text, nullable=True)  # What was happening
    outcome = Column(Text, nullable=True)  # What resulted
    importance = Column(Integer, default=5)  # 1-10 scale
    tags = Column(JSON, nullable=True)  # Categorization tags
    access_count = Column(Integer, default=0)  # How often recalled
    last_accessed = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class SemanticMemory(Base):
    """
    Semantic memories — learned facts, user preferences, domain knowledge.
    These are general knowledge items persisted across all conversations.
    """
    __tablename__ = "semantic_memories"

    id = Column(String, primary_key=True, default=_new_id)
    agent_config_id = Column(String, ForeignKey("agent_configs.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(100), nullable=False)  # preference, fact, pattern, correction, domain_knowledge
    key = Column(String(500), nullable=False)  # Short identifier
    value = Column(Text, nullable=False)  # The learned information
    confidence = Column(Integer, default=70)  # 0-100 confidence score
    source = Column(String(50), nullable=False, default="inferred")  # inferred, user_stated, feedback, correction
    reinforcement_count = Column(Integer, default=1)  # Times this was confirmed
    last_reinforced = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class LearningEvent(Base):
    """
    Learning event log — records what the agent learned and when.
    Provides an audit trail of the agent's knowledge evolution.
    """
    __tablename__ = "learning_events"

    id = Column(String, primary_key=True, default=_new_id)
    agent_config_id = Column(String, ForeignKey("agent_configs.id", ondelete="CASCADE"), nullable=False)
    thread_id = Column(String, nullable=True)
    event_type = Column(String(50), nullable=False)  # insight_extracted, feedback_processed, preference_learned, correction_applied, pattern_detected
    description = Column(Text, nullable=False)
    source_data = Column(JSON, nullable=True)  # The raw data that triggered learning
    memories_created = Column(JSON, nullable=True)  # IDs of memories created
    created_at = Column(DateTime, default=_utcnow)


class UserFeedback(Base):
    """
    User feedback on agent responses — thumbs up/down and corrections.
    Feeds into the learning engine.
    """
    __tablename__ = "user_feedback"

    id = Column(String, primary_key=True, default=_new_id)
    thread_id = Column(String, ForeignKey("threads.id", ondelete="CASCADE"), nullable=False)
    message_id = Column(String, nullable=False)
    agent_config_id = Column(String, ForeignKey("agent_configs.id", ondelete="SET NULL"), nullable=True)
    rating = Column(String(20), nullable=False)  # positive, negative
    correction = Column(Text, nullable=True)  # User's correction text
    original_response = Column(Text, nullable=True)  # What the agent said
    processed = Column(Boolean, default=False)  # Whether learning engine processed this
    created_at = Column(DateTime, default=_utcnow)
