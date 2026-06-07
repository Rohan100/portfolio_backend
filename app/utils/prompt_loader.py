"""
prompt_loader.py — Utility to load and render the system prompt template.

Reads system_prompt.txt once, caches it, and injects the knowledge base
at call time. Separating template from data makes the prompt easy to edit
without touching Python code.
"""

import os
import logging

logger = logging.getLogger(__name__)

_prompt_template: str | None = None


def _load_template(path: str) -> str:
    """Read and cache the raw prompt template from disk."""
    global _prompt_template

    if _prompt_template is None:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"System prompt file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            _prompt_template = f.read()
        logger.info("System prompt template loaded from: %s", path)

    return _prompt_template


def build_system_prompt(prompt_path: str, knowledge: str) -> str:
    """
    Load the system prompt template and inject the knowledge base.

    Args:
        prompt_path: Absolute path to system_prompt.txt.
        knowledge:   The combined knowledge string from knowledge_service.

    Returns:
        Fully rendered system prompt ready to send as the first message.
    """
    template = _load_template(prompt_path)
    return template.replace("{knowledge}", knowledge)
