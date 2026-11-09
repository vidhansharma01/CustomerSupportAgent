from __future__ import annotations

from typing import Annotated, Optional

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    conversation_id: str
    customer_id: Optional[str]
    customer_data: Optional[dict]
    tool_call_count: int
    escalated: bool
    ticket_id: Optional[str]
    sources: list[dict]
    final_answer: Optional[str]
