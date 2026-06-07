"""
message_builder.py — Utility to assemble the messages list sent to the LLM.

Centralises the logic for prepending the system prompt, trimming history,
and appending the current user message. This keeps groq_service.py clean
and makes it trivial to change history truncation logic in one place.
"""

from app.schemas.chat_request import HistoryMessage


def build_messages(
    system_prompt: str,
    history: list[HistoryMessage],
    user_message: str,
    max_history: int = 10,
) -> list[dict[str, str]]:
    """
    Assemble the full messages list in OpenAI chat format.

    Layout:
        [system, ...last N history turns, current user message]

    Args:
        system_prompt: The fully rendered system prompt string.
        history:       Previous conversation messages from the client.
        user_message:  The current message from the user.
        max_history:   Maximum number of history messages to include.
                       Older messages are dropped (FIFO trim from the left).

    Returns:
        List of message dicts ready to pass to any OpenAI-compatible LLM API.
    """
    # Trim history to the most recent N messages
    trimmed_history = history[-max_history:] if len(history) > max_history else history

    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt}
    ]

    for msg in trimmed_history:
        messages.append({"role": msg.role, "content": msg.content})

    messages.append({"role": "user", "content": user_message})

    return messages
