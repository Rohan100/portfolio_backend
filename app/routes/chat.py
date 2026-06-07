"""
chat.py — API routes for the portfolio chatbot.

Endpoints:
  POST /api/chat          — Full response (JSON)
  POST /api/chat/stream   — Streaming response (Server-Sent Events)
  GET  /api/knowledge     — List loaded knowledge files
  GET  /api/models        — Current LLM model info

All endpoints are rate-limited to 10 requests/minute per IP via slowapi.
"""

import logging
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.schemas.chat_request import ChatRequest
from app.schemas.chat_response import ChatResponse, KnowledgeResponse, ModelResponse
from app.services.groq_service import get_llm_service
from app.services.knowledge_service import get_knowledge, get_loaded_files
from app.utils.prompt_loader import build_system_prompt
from app.utils.message_builder import build_messages

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_system_prompt() -> str:
    """Build the system prompt by injecting the cached knowledge base."""
    knowledge = get_knowledge(settings.knowledge_dir)
    return build_system_prompt(settings.system_prompt_path, knowledge)


# ---------------------------------------------------------------------------
# POST /api/chat — non-streaming
# ---------------------------------------------------------------------------

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send a message and receive a full response",
    description=(
        "Sends a user message (with optional conversation history) to the AI "
        "and returns the complete response in one JSON payload."
    ),
)
@limiter.limit(settings.rate_limit)
async def chat(request: Request, body: ChatRequest) -> ChatResponse:
    """
    Non-streaming chat endpoint.

    Suitable for simple integrations where the client does not need real-time
    token streaming (e.g., mobile apps, simple React state).
    """
    logger.info(
        "POST /api/chat | ip=%s | msg_len=%d | history=%d",
        request.client.host if request.client else "unknown",
        len(body.message),
        len(body.history),
    )

    system_prompt = _get_system_prompt()
    messages = build_messages(
        system_prompt=system_prompt,
        history=body.history,
        user_message=body.message,
        max_history=settings.max_history_messages,
    )

    llm = get_llm_service()

    try:
        answer = await llm.generate_response(messages)
    except ValueError as exc:
        logger.error("LLM error in /api/chat: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return ChatResponse(answer=answer)


# ---------------------------------------------------------------------------
# POST /api/chat/stream — Server-Sent Events streaming
# ---------------------------------------------------------------------------

@router.post(
    "/chat/stream",
    summary="Send a message and receive a streaming response",
    description=(
        "Streams the AI response token-by-token using Server-Sent Events (SSE). "
        "Compatible with the Vercel AI SDK, Next.js fetch(), and ReadableStream."
    ),
    response_class=StreamingResponse,
)
@limiter.limit(settings.rate_limit)
async def chat_stream(request: Request, body: ChatRequest) -> StreamingResponse:
    """
    Streaming chat endpoint using Server-Sent Events.

    SSE format:
        data: <token>\\n\\n

    The [DONE] sentinel signals end-of-stream to the client.

    Compatible with:
      - Vercel AI SDK useChat() hook
      - Next.js fetch() + ReadableStream
      - Any SSE-aware client
    """
    logger.info(
        "POST /api/chat/stream | ip=%s | msg_len=%d | history=%d",
        request.client.host if request.client else "unknown",
        len(body.message),
        len(body.history),
    )

    system_prompt = _get_system_prompt()
    messages = build_messages(
        system_prompt=system_prompt,
        history=body.history,
        user_message=body.message,
        max_history=settings.max_history_messages,
    )

    llm = get_llm_service()

    async def token_generator():
        """
        Async generator that yields SSE-formatted chunks.
        Errors inside the stream are surfaced as error: events.
        """
        try:
            async for chunk in llm.generate_stream(messages):
                # SSE format: "data: <payload>\n\n"
                yield f"data: {chunk}\n\n"
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Stream error: %s", exc)
            yield f"event: error\ndata: {str(exc)}\n\n"
        finally:
            # Signal end-of-stream (compatible with Vercel AI SDK)
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        token_generator(),
        media_type="text/event-stream",
        headers={
            # Prevent buffering by proxies / nginx
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ---------------------------------------------------------------------------
# GET /api/knowledge — list available knowledge files
# ---------------------------------------------------------------------------

@router.get(
    "/knowledge",
    response_model=KnowledgeResponse,
    summary="List loaded knowledge files",
    description="Returns the filenames of all Markdown files loaded into the knowledge base.",
)
async def get_knowledge_files() -> KnowledgeResponse:
    files = get_loaded_files()
    logger.info("GET /api/knowledge | %d files", len(files))
    return KnowledgeResponse(files=files, total=len(files))


# ---------------------------------------------------------------------------
# GET /api/models — current model info
# ---------------------------------------------------------------------------

@router.get(
    "/models",
    response_model=ModelResponse,
    summary="Get current LLM model",
    description="Returns the currently configured Groq model and provider.",
)
async def get_model_info() -> ModelResponse:
    logger.info("GET /api/models | model=%s", settings.model)
    return ModelResponse(current_model=settings.model, provider="groq")
