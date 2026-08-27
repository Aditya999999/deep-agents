"""
ForgeX — Learning Service

Self-learning engine that extracts insights from conversations,
processes user feedback, and builds the agent's knowledge over time.

Learning Triggers:
1. Post-conversation — Extract key insights after a thread ends/idles
2. User feedback — Process thumbs up/down and corrections
3. Pattern detection — Identify recurring themes across conversations
4. Explicit teaching — User directly tells the agent to remember something
"""

import re
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import (
    LearningEvent, UserFeedback, ThreadMessage, SemanticMemory
)
from app.application.memory_service import MemoryService
from app.core.logging import get_logger

logger = get_logger("application.learning_service")

# Patterns that indicate the user is teaching the agent
TEACHING_PATTERNS = [
    r"(?:remember|note|learn)\s+that\s+(.+)",
    r"(?:my|i)\s+(?:prefer|like|want|need)\s+(.+)",
    r"(?:always|never|don't)\s+(.+)",
    r"(?:keep in mind|for future reference|fyi|note to self)\s*[:\-]?\s*(.+)",
    r"(?:i am|i'm|my name is|call me)\s+(.+)",
    r"(?:my (?:email|phone|address|company|role|title) is)\s+(.+)",
]

# Patterns that indicate a correction
CORRECTION_PATTERNS = [
    r"(?:no|wrong|incorrect|actually|not quite),?\s+(.+)",
    r"(?:that's not right|that's wrong),?\s+(.+)",
    r"(?:i meant|i mean|what i meant was)\s+(.+)",
    r"(?:please correct|fix|update)\s+(.+)",
]


class LearningService:
    """
    Self-learning engine for the agent.

    Automatically extracts and stores knowledge from interactions.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.memory_service = MemoryService(session)

    # ──────────────────────────────────────────────────────────────────────
    # User Feedback Processing
    # ──────────────────────────────────────────────────────────────────────

    async def submit_feedback(
        self,
        thread_id: str,
        message_id: str,
        rating: str,
        correction: Optional[str] = None,
        original_response: Optional[str] = None,
        agent_config_id: Optional[str] = None,
    ) -> UserFeedback:
        """Submit user feedback on an agent response."""
        feedback = UserFeedback(
            thread_id=thread_id,
            message_id=message_id,
            agent_config_id=agent_config_id,
            rating=rating,
            correction=correction,
            original_response=original_response,
            processed=False,
        )
        self.session.add(feedback)
        await self.session.flush()

        # Process immediately if we have an agent config
        if agent_config_id:
            await self._process_feedback(feedback, agent_config_id)

        logger.info(f"Feedback submitted: {rating} for message {message_id}")
        return feedback

    async def _process_feedback(self, feedback: UserFeedback, agent_config_id: str) -> None:
        """Process a piece of feedback into learning."""
        memories_created = []

        if feedback.rating == "negative" and feedback.correction:
            # Learn from correction
            memory = await self.memory_service.store_semantic(
                agent_config_id=agent_config_id,
                category="correction",
                key=f"correction_{feedback.id[:8]}",
                value=f"User corrected: {feedback.correction}. Original response was: {(feedback.original_response or '')[:200]}",
                confidence=90,
                source="correction",
            )
            memories_created.append(memory.id)

        elif feedback.rating == "positive":
            # Reinforce the approach used
            if feedback.original_response:
                memory = await self.memory_service.store_semantic(
                    agent_config_id=agent_config_id,
                    category="pattern",
                    key=f"positive_pattern_{feedback.id[:8]}",
                    value=f"User liked this response style/approach: {feedback.original_response[:300]}",
                    confidence=60,
                    source="feedback",
                )
                memories_created.append(memory.id)

        # Log the learning event
        event = LearningEvent(
            agent_config_id=agent_config_id,
            thread_id=feedback.thread_id,
            event_type="feedback_processed",
            description=f"Processed {feedback.rating} feedback" + (
                f" with correction: {feedback.correction[:100]}" if feedback.correction else ""
            ),
            source_data={
                "feedback_id": feedback.id,
                "rating": feedback.rating,
                "has_correction": bool(feedback.correction),
            },
            memories_created=memories_created,
        )
        self.session.add(event)

        # Mark feedback as processed
        feedback.processed = True
        await self.session.flush()

    # ──────────────────────────────────────────────────────────────────────
    # Conversation Insight Extraction
    # ──────────────────────────────────────────────────────────────────────

    async def extract_insights_from_thread(
        self, agent_config_id: str, thread_id: str, messages: list[dict]
    ) -> list[dict]:
        """
        Analyze a conversation and extract learnable insights.

        Called after a conversation ends or during idle periods.
        """
        insights = []

        for msg in messages:
            if msg.get("role") != "user":
                continue

            content = msg.get("content", "")
            if not content:
                continue

            # Check for explicit teaching statements
            for pattern in TEACHING_PATTERNS:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    learned_info = match.group(1).strip()
                    if len(learned_info) > 5:
                        insight = await self._store_teaching(
                            agent_config_id, thread_id, content, learned_info
                        )
                        insights.append(insight)

            # Check for preference expressions
            preference = self._detect_preference(content)
            if preference:
                insight = await self._store_preference(
                    agent_config_id, thread_id, preference
                )
                insights.append(insight)

        # Store an episodic memory of this conversation
        if messages:
            user_messages = [m["content"] for m in messages if m.get("role") == "user" and m.get("content")]
            if user_messages:
                topic = user_messages[0][:100] if user_messages else "General conversation"
                await self.memory_service.store_episodic(
                    agent_config_id=agent_config_id,
                    thread_id=thread_id,
                    summary=f"Conversation about: {topic}",
                    context=f"User asked {len(user_messages)} question(s)",
                    outcome="Conversation completed",
                    importance=5,
                    tags=self._extract_tags(user_messages),
                )

        return insights

    async def _store_teaching(
        self, agent_config_id: str, thread_id: str, full_text: str, learned: str
    ) -> dict:
        """Store an explicitly taught fact."""
        # Categorize the teaching
        category = "fact"
        if any(w in learned.lower() for w in ["prefer", "like", "want", "favorite"]):
            category = "preference"
        elif any(w in learned.lower() for w in ["i am", "my name", "i'm", "my email"]):
            category = "user_info"

        memory = await self.memory_service.store_semantic(
            agent_config_id=agent_config_id,
            category=category,
            key=self._make_key(learned),
            value=learned,
            confidence=95,  # High confidence — user explicitly stated it
            source="user_stated",
        )

        event = LearningEvent(
            agent_config_id=agent_config_id,
            thread_id=thread_id,
            event_type="insight_extracted",
            description=f"Learned from user statement: {learned[:100]}",
            source_data={"original_text": full_text[:300]},
            memories_created=[memory.id],
        )
        self.session.add(event)
        await self.session.flush()

        return {
            "type": "teaching",
            "category": category,
            "learned": learned,
            "memory_id": memory.id,
        }

    async def _store_preference(
        self, agent_config_id: str, thread_id: str, preference: dict
    ) -> dict:
        """Store a detected user preference."""
        memory = await self.memory_service.store_semantic(
            agent_config_id=agent_config_id,
            category="preference",
            key=preference["key"],
            value=preference["value"],
            confidence=70,
            source="inferred",
        )

        event = LearningEvent(
            agent_config_id=agent_config_id,
            thread_id=thread_id,
            event_type="preference_learned",
            description=f"Inferred preference: {preference['value'][:100]}",
            memories_created=[memory.id],
        )
        self.session.add(event)
        await self.session.flush()

        return {
            "type": "preference",
            "key": preference["key"],
            "value": preference["value"],
            "memory_id": memory.id,
        }

    def _detect_preference(self, text: str) -> Optional[dict]:
        """Detect preference expressions in user text."""
        lower = text.lower()
        preference_triggers = [
            (r"i (?:prefer|like|love|enjoy)\s+(.+?)(?:\.|$)", "user_preference"),
            (r"(?:use|use|give me|show me)\s+(\w+)\s+(?:format|style|mode)", "format_preference"),
            (r"(?:make it|keep it)\s+(.+?)(?:\.|$)", "style_preference"),
        ]
        for pattern, pref_type in preference_triggers:
            match = re.search(pattern, lower)
            if match:
                value = match.group(1).strip()
                if len(value) > 3:
                    return {
                        "key": f"{pref_type}_{self._make_key(value)}",
                        "value": f"User prefers: {value}",
                    }
        return None

    def _make_key(self, text: str) -> str:
        """Create a short key from text."""
        words = re.sub(r'[^a-z0-9\s]', '', text.lower()).split()
        return "_".join(words[:5])

    def _extract_tags(self, messages: list[str]) -> list[str]:
        """Extract topic tags from messages."""
        combined = " ".join(messages).lower()
        tags = []
        tag_keywords = {
            "code": ["code", "programming", "function", "debug", "error"],
            "data": ["data", "database", "sql", "csv", "json"],
            "analysis": ["analyze", "analysis", "report", "summary"],
            "writing": ["write", "draft", "email", "document"],
            "math": ["calculate", "math", "formula", "equation"],
            "search": ["search", "find", "look up", "research"],
            "design": ["design", "ui", "layout", "style"],
        }
        for tag, keywords in tag_keywords.items():
            if any(kw in combined for kw in keywords):
                tags.append(tag)
        return tags[:5]

    # ──────────────────────────────────────────────────────────────────────
    # Learning Log
    # ──────────────────────────────────────────────────────────────────────

    async def get_learning_log(
        self, agent_config_id: str, limit: int = 30
    ) -> list[LearningEvent]:
        """Get the learning event log for an agent."""
        stmt = (
            select(LearningEvent)
            .where(LearningEvent.agent_config_id == agent_config_id)
            .order_by(desc(LearningEvent.created_at))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_learning_stats(self, agent_config_id: str) -> dict:
        """Get learning statistics."""
        # Count by event type
        stmt = select(
            LearningEvent.event_type,
            func.count(LearningEvent.id)
        ).where(
            LearningEvent.agent_config_id == agent_config_id
        ).group_by(LearningEvent.event_type)

        result = await self.session.execute(stmt)
        type_counts = {row[0]: row[1] for row in result.all()}

        # Feedback stats
        fb_stmt = select(
            UserFeedback.rating,
            func.count(UserFeedback.id)
        ).where(
            UserFeedback.agent_config_id == agent_config_id
        ).group_by(UserFeedback.rating)

        fb_result = await self.session.execute(fb_stmt)
        feedback_counts = {row[0]: row[1] for row in fb_result.all()}

        memory_stats = await self.memory_service.get_memory_stats(agent_config_id)

        return {
            "learning_events": type_counts,
            "feedback": feedback_counts,
            "memory": memory_stats,
            "total_events": sum(type_counts.values()),
        }
