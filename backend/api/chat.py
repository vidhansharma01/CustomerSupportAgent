from __future__ import annotations

import logging
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import HumanMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from backend.agent.graph import agent_graph, run_agent
from backend.database import get_db
from backend.models.ticket import ConversationMessage
from backend.schemas.chat import ChatRequest, ChatResponse, SourceDoc, StreamChunk
from backend.schemas.ticket import ConversationMessageRead

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chat"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _persist_message(
    session: AsyncSession,
    conversation_id: str,
    role: str,
    content: str,
    tool_name: str | None = None,
) -> None:
    """Save a conversation message to the database."""
    msg = ConversationMessage(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        role=role,
        content=content,
        tool_name=tool_name,
    )
    session.add(msg)
    await session.commit()


# ---------------------------------------------------------------------------
# POST /api/chat
# ---------------------------------------------------------------------------


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """Send a message to the AI agent and receive a response."""
    conversation_id = request.conversation_id or str(uuid.uuid4())

    # Persist user message
    await _persist_message(db, conversation_id, "user", request.message)

    # Build initial state
    state_input = {
        "messages": [HumanMessage(content=request.message)],
        "conversation_id": conversation_id,
        "customer_id": str(request.customer_id) if request.customer_id else None,
        "customer_data": None,
        "tool_call_count": 0,
        "escalated": False,
        "ticket_id": None,
        "sources": [],
        "final_answer": None,
    }

    config = {"configurable": {"thread_id": conversation_id}}

    try:
        final_state = await run_agent(state_input, config)
    except Exception as exc:
        logger.exception("Agent error for conversation %s: %s", conversation_id, exc)
        raise HTTPException(status_code=500, detail=f"Agent error: {exc}") from exc

    answer = final_state.get("final_answer") or "I'm sorry, I couldn't generate a response."
    escalated = final_state.get("escalated", False)
    ticket_id_str = final_state.get("ticket_id")
    sources_raw = final_state.get("sources", [])

    # Persist assistant message
    await _persist_message(db, conversation_id, "assistant", answer)

    sources = [
        SourceDoc(
            title=s.get("title", "Unknown"),
            category=s.get("category", "unknown"),
            relevance=float(s.get("score", 0.0)),
        )
        for s in sources_raw
    ]

    ticket_uuid: uuid.UUID | None = None
    if ticket_id_str:
        try:
            ticket_uuid = uuid.UUID(ticket_id_str)
        except ValueError:
            ticket_uuid = None

    return ChatResponse(
        conversation_id=conversation_id,
        message=answer,
        sources=sources,
        escalated=escalated,
        ticket_id=ticket_uuid,
    )


# ---------------------------------------------------------------------------
# GET /api/chat/stream/{conversation_id}
# ---------------------------------------------------------------------------


@router.get("/stream/{conversation_id}")
async def stream_chat(
    conversation_id: str,
    message: str,
    customer_id: str | None = None,
) -> EventSourceResponse:
    """SSE endpoint for streaming agent responses token-by-token."""

    async def event_generator() -> AsyncGenerator[dict, None]:
        config = {"configurable": {"thread_id": conversation_id}}
        state_input = {
            "messages": [HumanMessage(content=message)],
            "conversation_id": conversation_id,
            "customer_id": customer_id,
            "customer_data": None,
            "tool_call_count": 0,
            "escalated": False,
            "ticket_id": None,
            "sources": [],
            "final_answer": None,
        }

        try:
            async for event in agent_graph.astream_events(
                state_input, config=config, version="v2"
            ):
                kind = event.get("event", "")

                if kind == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and chunk.content:
                        yield {
                            "data": StreamChunk(
                                type="token",
                                content=chunk.content,
                                metadata={},
                            ).model_dump_json()
                        }

                elif kind == "on_tool_start":
                    tool_name = event.get("name", "unknown_tool")
                    yield {
                        "data": StreamChunk(
                            type="tool_call",
                            content=f"Calling tool: {tool_name}",
                            metadata={"tool": tool_name},
                        ).model_dump_json()
                    }

            yield {
                "data": StreamChunk(
                    type="done",
                    content="",
                    metadata={},
                ).model_dump_json()
            }

        except Exception as exc:
            logger.exception("SSE stream error: %s", exc)
            yield {
                "data": StreamChunk(
                    type="error",
                    content=str(exc),
                    metadata={},
                ).model_dump_json()
            }

    return EventSourceResponse(event_generator())


# ---------------------------------------------------------------------------
# GET /api/chat/history/{conversation_id}
# ---------------------------------------------------------------------------


@router.get("/history/{conversation_id}", response_model=list[ConversationMessageRead])
async def get_history(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[ConversationMessage]:
    """Return all stored messages for a conversation."""
    result = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.created_at.asc())
    )
    return list(result.scalars().all())
