"""
groq_service.py — LLM interaction layer using the Groq SDK.

Architecture:
  BaseLLMService (ABC) — defines the contract all LLM providers must implement.
  GroqService          — concrete implementation using the Groq Python SDK.

To add OpenAI, Gemini, or OpenRouter:
  1. Create a new class inheriting BaseLLMService.
  2. Implement generate_response() and generate_stream().
  3. Swap the provider in get_llm_service() below — no route changes needed.
"""

import logging
from abc import ABC, abstractmethod
from typing import AsyncGenerator

from groq import AsyncGroq, APIError, APITimeoutError, RateLimitError

from app.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Abstract Base — the contract every LLM provider must fulfil
# ---------------------------------------------------------------------------

class BaseLLMService(ABC):
    """
    Provider-agnostic interface for LLM services.

    Both generate_response and generate_stream receive messages in the
    OpenAI chat format so they are portable across providers.
    """

    @abstractmethod
    async def generate_response(
        self,
        messages: list[dict[str, str]],
    ) -> str:
        """
        Generate a complete (non-streaming) response.

        Args:
            messages: Full message list including system prompt, history,
                      and the latest user message.

        Returns:
            The assistant's response as a plain string.
        """
        ...

    @abstractmethod
    async def generate_stream(
        self,
        messages: list[dict[str, str]],
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response, yielding tokens as they arrive.

        Args:
            messages: Full message list (same format as generate_response).

        Yields:
            Individual text chunks / tokens from the LLM.
        """
        ...


# ---------------------------------------------------------------------------
# Groq Implementation
# ---------------------------------------------------------------------------

class GroqService(BaseLLMService):
    """
    Concrete LLM service backed by the Groq API.

    Uses AsyncGroq for non-blocking I/O — critical for FastAPI's async model.
    The client is instantiated once and reused across requests.
    """

    def __init__(self) -> None:
        self._client = AsyncGroq(api_key=settings.groq_api_key)
        self._model = settings.model
        logger.info("GroqService initialised with model: %s", self._model)

    async def generate_response(
        self,
        messages: list[dict[str, str]],
    ) -> str:
        """
        Call Groq and return the full response text.

        Raises:
            ValueError: On Groq API / timeout errors (caller handles HTTP codes).
        """
        try:
            logger.debug("Sending %d messages to Groq (non-streaming).", len(messages))
            completion = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,  # type: ignore[arg-type]
                temperature=0.7,
                max_tokens=1024,
            )
            answer = completion.choices[0].message.content or ""
            logger.debug("Groq response received (%d chars).", len(answer))
            return answer

        except RateLimitError as exc:
            logger.error("Groq rate limit exceeded: %s", exc)
            raise ValueError("The AI service is currently rate-limited. Please try again shortly.") from exc

        except APITimeoutError as exc:
            logger.error("Groq request timed out: %s", exc)
            raise ValueError("The AI service timed out. Please try again.") from exc

        except APIError as exc:
            logger.error("Groq API error (%s): %s", exc.status_code, exc.message)
            raise ValueError(f"AI service error: {exc.message}") from exc

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
    ) -> AsyncGenerator[str, None]:
        """
        Call Groq with streaming enabled and yield token chunks.

        Compatible with FastAPI's StreamingResponse and the Vercel AI SDK
        (text/event-stream format is handled by the route layer, not here).

        Yields:
            Text delta strings from each streaming chunk.
        """
        try:
            logger.debug("Sending %d messages to Groq (streaming).", len(messages))
            stream = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,  # type: ignore[arg-type]
                temperature=0.7,
                max_tokens=1024,
                stream=True,
            )

            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta

        except RateLimitError as exc:
            logger.error("Groq rate limit exceeded during stream: %s", exc)
            yield "\n\n[Error: The AI service is currently rate-limited. Please try again shortly.]"

        except APITimeoutError as exc:
            logger.error("Groq stream timed out: %s", exc)
            yield "\n\n[Error: The AI service timed out. Please try again.]"

        except APIError as exc:
            logger.error("Groq API error during stream (%s): %s", exc.status_code, exc.message)
            yield f"\n\n[Error: AI service error — {exc.message}]"


# ---------------------------------------------------------------------------
# Service factory — swap providers here without touching routes
# ---------------------------------------------------------------------------

def get_llm_service() -> BaseLLMService:
    """
    Dependency-injected factory for the active LLM service.

    To switch providers, change the return value here:
      return OpenAIService()   # future
      return GeminiService()   # future
      return OpenRouterService()  # future
    """
    return GroqService()
