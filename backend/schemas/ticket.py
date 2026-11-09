from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TicketCreate(BaseModel):
    customer_id: Optional[UUID] = None
    conversation_id: str
    subject: str
    description: str
    priority: str = "medium"


class TicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    resolved_at: Optional[datetime] = None


class TicketRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: Optional[UUID]
    conversation_id: str
    subject: str
    description: str
    priority: str
    status: str
    assigned_to: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime]


class ConversationMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: str
    role: str
    content: str
    tool_name: Optional[str]
    created_at: datetime
