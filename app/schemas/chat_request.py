"""
chat_request.py — Pydantic schemas for incoming chat requests.

Defines the shape of requests accepted by POST /api/chat and POST /api/chat/stream.
Conversation history follows the OpenAI message format for maximum compatibility.
"""

from pydantic import BaseModel, Field
from typing import Literal


class HistoryMessage(BaseModel):
    """
    A single message in the conversation history.
    Follows the OpenAI chat message format — compatible with most LLM providers.
    """

    role: Literal["user", "assistant"] = Field(
        ...,
        description="The role of the message sender: 'user' or 'assistant'.",
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=4096,
        description="The text content of the message.",
    )


class ChatRequest(BaseModel):
    """
    Request body for both /api/chat and /api/chat/stream endpoints.

    The client is responsible for maintaining and sending history — this keeps
    the backend stateless and horizontally scalable.
    """

    message: str = Field(
        ...,
        min_length=1,
        max_length=2048,
        description="The user's current message to the chatbot.",
        examples=["What projects have you built?"],
    )
    history: list[HistoryMessage] = Field(
        default_factory=list,
        description=(
            "Previous conversation turns in OpenAI message format. "
            "Only the last 10 messages are used; older messages are trimmed."
        ),
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Tell me about your skills",
                "history": [
                    {"role": "user", "content": "Hi!"},
                    {"role": "assistant", "content": "Hello! How can I help you?"},
                ],
            }
        }
