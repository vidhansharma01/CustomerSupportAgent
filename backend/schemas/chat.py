from __future__ import annotations

from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SourceDoc(BaseModel):
    title: str
    category: str
    relevance: float


class ChatRequest(BaseModel):
    conversation_id: str
    message: str
    customer_id: Optional[UUID] = None


class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    sources: list[SourceDoc] = []
    escalated: bool = False
    ticket_id: Optional[UUID] = None


class StreamChunk(BaseModel):
    type: Literal["token", "tool_call", "done", "error"]
    content: str
    metadata: dict = {}
