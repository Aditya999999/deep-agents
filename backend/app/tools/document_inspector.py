"""
ForgeX — Document Inspector Tool

Inspect uploaded documents and extract text/metadata per spec §9.4.
Handles plain text, markdown, and provides metadata for binary formats.
Built as a LangChain tool via @tool decorator.
"""

import json
from pathlib import Path

from langchain_core.tools import tool

from app.core.logging import get_logger

logger = get_logger("tools.document_inspector")

# Max text extraction size
MAX_EXTRACT_CHARS = 50000


@tool
def document_inspector(file_path: str) -> str:
    """Inspect an uploaded document file — extract text content, metadata, and file information.
    Handles plain text, markdown, CSV, JSON, code files, and provides metadata for
    binary formats (PDF, DOCX, images).

    Args:
        file_path: Path to the document file in the agent's managed filesystem
    """
    try:
        if not file_path:
            return "Error: No file path provided"

        path = Path(file_path)
        if not path.exists():
            return f"Error: File not found — {path.name}"

        stat = path.stat()
        result = {
            "filename": path.name,
            "extension": path.suffix.lower(),
            "size_bytes": stat.st_size,
            "size_human": _human_size(stat.st_size),
        }

        ext = path.suffix.lower()

        # Text-based formats — extract content
        text_extensions = (
            ".txt", ".md", ".markdown", ".csv", ".json", ".xml",
            ".yaml", ".yml", ".py", ".js", ".ts", ".html", ".css",
            ".sql", ".sh", ".bat", ".log", ".ini", ".toml", ".cfg",
        )
        if ext in text_extensions:
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
                result["content_type"] = "text"
                result["text"] = text[:MAX_EXTRACT_CHARS]
                result["total_characters"] = len(text)
                result["line_count"] = text.count("\n") + 1
                result["truncated"] = len(text) > MAX_EXTRACT_CHARS
            except Exception as e:
                result["error"] = f"Failed to read text: {str(e)}"

        # Binary document formats — metadata only
        elif ext in (".pdf", ".docx", ".doc", ".xlsx", ".pptx"):
            result["content_type"] = "binary_document"
            result["note"] = (
                f"Binary document format ({ext}). "
                "Full parsing requires additional libraries. "
                "File is accessible in the agent filesystem for reference."
            )

        # Image formats
        elif ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"):
            result["content_type"] = "image"
            result["note"] = f"Image file ({ext}). Viewable by the model if supported."

        else:
            result["content_type"] = "unknown"
            result["note"] = f"Unknown file format ({ext})"

        logger.info(f"Inspected document: {path.name} ({result.get('content_type', 'unknown')})")
        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Document inspection error: {e}")
        return f"Error: Inspection failed — {str(e)}"


def _human_size(size_bytes: int) -> str:
    """Convert bytes to human-readable size."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
