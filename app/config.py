"""
config.py — Application configuration loaded from environment variables.

Uses pydantic-settings pattern for type-safe settings with dotenv support.
All settings are loaded once at startup and shared via dependency injection.
"""

import os
from dotenv import load_dotenv

# Load .env file before anything else
load_dotenv()


class Settings:
    """
    Central settings object. Reads from environment variables (or .env file).
    Add new config fields here — never scatter os.getenv() calls across the codebase.
    """

    # Groq API
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    model: str = os.getenv("MODEL", "llama-3.3-70b-versatile")

    # Server
    app_title: str = "Portfolio AI Chatbot API"
    app_version: str = "1.0.0"
    app_description: str = (
        "A production-ready FastAPI backend powering a personal portfolio chatbot "
        "backed by Groq LLM. Supports streaming, conversation history, and a "
        "swappable LLM architecture for future providers."
    )

    # CORS — extend this list when deploying to production domains
    cors_origins: list[str] = [
        "http://localhost:3000",   # Next.js default
        "http://localhost:5173",   # Vite default
    ]

    # Rate limiting (slowapi)
    rate_limit: str = "10/minute"

    # Paths
    knowledge_dir: str = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "knowledge"
    )
    system_prompt_path: str = os.path.join(
        os.path.dirname(__file__), "prompts", "system_prompt.txt"
    )

    # Chat history
    max_history_messages: int = 10

    def validate(self) -> None:
        """Raise at startup if critical env vars are missing."""
        if not self.groq_api_key:
            raise ValueError(
                "GROQ_API_KEY is not set. "
                "Please add it to your .env file or environment."
            )


# Singleton — import this everywhere
settings = Settings()
