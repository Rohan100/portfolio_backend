"""
knowledge_service.py — Loads and caches the portfolio knowledge base.

Reads all .md files from the knowledge/ directory, combines them into a single
string, and caches the result in memory. The cache is populated once at startup
and lives for the lifetime of the server process.

To reload knowledge without restarting the server, call reload_knowledge().
"""

import os
import glob
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

# Module-level cache — populated on first access or explicit reload
_knowledge_cache: str | None = None
_loaded_files: list[str] = []


def load_knowledge(knowledge_dir: str) -> str:
    """
    Read all .md files from knowledge_dir and combine them into one string.

    Each file is prefixed with a Markdown header derived from its filename
    so the LLM can distinguish sections (e.g., "## About", "## Skills").

    Args:
        knowledge_dir: Absolute path to the directory containing .md files.

    Returns:
        Combined knowledge string ready to be injected into the system prompt.

    Raises:
        FileNotFoundError: If knowledge_dir does not exist.
    """
    global _knowledge_cache, _loaded_files

    if not os.path.isdir(knowledge_dir):
        raise FileNotFoundError(
            f"Knowledge directory not found: {knowledge_dir}"
        )

    md_files = sorted(glob.glob(os.path.join(knowledge_dir, "*.md")))

    if not md_files:
        logger.warning("No .md files found in knowledge directory: %s", knowledge_dir)
        _knowledge_cache = ""
        _loaded_files = []
        return ""

    sections: list[str] = []
    loaded: list[str] = []

    for filepath in md_files:
        filename = os.path.basename(filepath)
        section_name = os.path.splitext(filename)[0].replace("_", " ").title()

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
            sections.append(f"## {section_name}\n\n{content}")
            loaded.append(filename)
            logger.info("Loaded knowledge file: %s", filename)
        except OSError as exc:
            logger.error("Failed to read %s: %s", filepath, exc)

    _knowledge_cache = "\n\n---\n\n".join(sections)
    _loaded_files = loaded

    logger.info(
        "Knowledge base loaded: %d file(s), %d characters total.",
        len(loaded),
        len(_knowledge_cache),
    )
    return _knowledge_cache


def get_knowledge(knowledge_dir: str) -> str:
    """
    Return cached knowledge. Loads from disk if not yet cached.

    This is the primary function used by services — it never hits disk
    after the first call unless reload_knowledge() is explicitly invoked.

    Args:
        knowledge_dir: Path to the knowledge directory (from settings).

    Returns:
        Combined knowledge string.
    """
    global _knowledge_cache

    if _knowledge_cache is None:
        load_knowledge(knowledge_dir)

    return _knowledge_cache or ""


def reload_knowledge(knowledge_dir: str) -> str:
    """
    Force-reload knowledge from disk, bypassing the cache.
    Useful for hot-reloading during development without restarting the server.

    Args:
        knowledge_dir: Path to the knowledge directory.

    Returns:
        Freshly loaded knowledge string.
    """
    global _knowledge_cache
    _knowledge_cache = None  # Invalidate cache
    return load_knowledge(knowledge_dir)


def get_loaded_files() -> list[str]:
    """Return the list of filenames that are currently cached."""
    return _loaded_files.copy()
