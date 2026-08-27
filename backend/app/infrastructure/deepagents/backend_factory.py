"""
ForgeX — Backend Factory

Manages StateBackend and filesystem backend configurations per spec §6.3.
"""

from typing import Any, Dict
from app.core.logging import get_logger

logger = get_logger("deepagents.backend_factory")


class BackendFactory:
    """Constructs virtual filesystem and state backends for Deep Agents."""

    @staticmethod
    def create_backend(mode: str = "state", options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create backend configuration dictionary.
        
        Args:
            mode: "state" for ephemeral thread-local or "persistent" for filesystem-backed
            options: Additional backend options
        """
        opts = options or {}
        if mode == "persistent":
            logger.info("Configuring persistent filesystem backend.")
            return {"type": "persistent", **opts}
        
        logger.info("Configuring thread-local StateBackend.")
        return {"type": "state", **opts}
