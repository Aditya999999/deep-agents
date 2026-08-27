"""
ForgeX — Skill Loader

Validates skill directories and SKILL.md per spec §7.1 & §1.2 (#4820).
Ensures parent directory structure is validated and paths cannot escape data root.
"""

from pathlib import Path
from typing import Dict, List, Optional
import yaml

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("deepagents.skill_loader")


class SkillLoader:
    """Discovers, validates and loads skills from filesystem."""

    def __init__(self, data_root: Optional[str] = None):
        self.data_root = Path(data_root or settings.data_root).resolve()

    def get_agent_skills_dir(self, agent_id: str) -> Path:
        """Get the parent directory containing all skill directories for an agent."""
        skills_dir = (self.data_root / "agents" / agent_id / "skills").resolve()
        skills_dir.mkdir(parents=True, exist_ok=True)
        return skills_dir

    def validate_skill_path(self, agent_id: str, skill_dir_name: str) -> Path:
        """Validate that skill path does not escape the agent skill storage root."""
        parent_dir = self.get_agent_skills_dir(agent_id)
        target_dir = (parent_dir / skill_dir_name).resolve()

        if not str(target_dir).startswith(str(parent_dir)):
            raise ValueError(f"Path traversal detected: {skill_dir_name} escapes agent root")

        return target_dir

    def discover_skills(self, agent_id: str) -> List[Dict[str, any]]:
        """
        Discover all skills in the agent's skills parent container.
        Validates presence of SKILL.md per spec §7.1.
        """
        parent_dir = self.get_agent_skills_dir(agent_id)
        discovered = []

        if not parent_dir.exists():
            return discovered

        for child in parent_dir.iterdir():
            if child.is_dir():
                skill_md = child / "SKILL.md"
                if skill_md.exists() and skill_md.is_file():
                    content = skill_md.read_text(encoding="utf-8")
                    frontmatter, body = self._parse_skill_md(content)
                    discovered.append({
                        "name": frontmatter.get("name", child.name),
                        "description": frontmatter.get("description", ""),
                        "directory_name": child.name,
                        "path": str(child),
                        "frontmatter": frontmatter,
                        "content": body,
                    })

        return discovered

    def _parse_skill_md(self, content: str) -> tuple[Dict[str, any], str]:
        """Extract YAML frontmatter and markdown body from SKILL.md."""
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    fm = yaml.safe_load(parts[1]) or {}
                    body = parts[2].strip()
                    return fm, body
                except Exception as e:
                    logger.warning(f"Failed to parse YAML frontmatter: {e}")
        return {}, content
