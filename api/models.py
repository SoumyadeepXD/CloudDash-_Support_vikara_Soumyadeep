from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from models.state import ConversationState


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    trace_id: str
    current_agent: str
    response: str
    citations: list[dict[str, Any]] = Field(default_factory=list)
    handover: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConversationStateResponse(BaseModel):
    state: ConversationState
