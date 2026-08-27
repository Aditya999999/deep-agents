"""
ForgeX — Checkpoint Factory

Manages LangGraph SQLite checkpointer instances per spec §8.1.
Uses AsyncSqliteSaver for persistent thread states.
"""

from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("deepagents.checkpoint_factory")


class CheckpointFactory:
    """Provides SQLite checkpointer instances for thread persistence."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.checkpoint_db_path

    def get_checkpoint_db_path(self) -> str:
        """Ensure parent directory exists and return SQLite db path."""
        p = Path(self.db_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        return str(p.resolve())
