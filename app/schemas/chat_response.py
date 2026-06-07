"""
chat_response.py — Pydantic schemas for outgoing chat responses.

Defines the response shapes returned by the chat endpoints.
Streaming endpoints return plain text/event-stream — no Pydantic model needed there.
"""

from pydantic import BaseModel, Field


class ChatResponse(BaseModel):
    """
    Response body for POST /api/chat (non-streaming).

    The answer field contains the full LLM response, potentially
    formatted in Markdown for rich rendering on the frontend.
    """

    answer: str = Field(
        ...,
        description="The AI assistant's response, possibly Markdown-formatted.",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "answer": (
                    "I've built several projects including:\n\n"
                    "- **PortfolioBot** — An AI chatbot for my portfolio\n"
                    "- **TaskFlow** — A full-stack task management app\n\n"
                    "You can find them on my [GitHub](https://github.com/example)."
                )
            }
        }


class HealthResponse(BaseModel):
    """Response body for GET /health."""

    status: str = Field(default="ok", description="Health status of the API.")


class KnowledgeResponse(BaseModel):
    """Response body for GET /api/knowledge."""

    files: list[str] = Field(
        ...,
        description="List of available markdown knowledge files.",
    )
    total: int = Field(..., description="Total number of knowledge files loaded.")


class ModelResponse(BaseModel):
    """Response body for GET /api/models."""

    current_model: str = Field(
        ..., description="The currently configured Groq model ID."
    )
    provider: str = Field(default="groq", description="The LLM provider being used.")
