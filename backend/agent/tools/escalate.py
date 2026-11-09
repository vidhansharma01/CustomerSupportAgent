from __future__ import annotations

import json
import logging
import uuid
from typing import Literal

from langchain_core.tools import tool
from pydantic import BaseModel, ValidationError

from backend.database import AsyncSessionLocal
from backend.models.ticket import SupportTicket

logger = logging.getLogger(__name__)


class EscalationRequest(BaseModel):
    reason: str
    priority: Literal["low", "medium", "high", "urgent"] = "medium"
    summary: str
    conversation_id: str = ""
    customer_id: str | None = None


@tool
async def escalate_to_human(escalation_json: str) -> str:
    """Escalate the conversation to a human support agent.

    Use this when the issue is complex, the customer is very frustrated,
    or the agent cannot resolve the problem autonomously.

    Args:
        escalation_json: JSON string with keys:
            - reason (str): Why escalation is needed.
            - priority (str): low / medium / high / urgent.
            - summary (str): Brief summary of the conversation and issue.
            - conversation_id (str, optional): Session conversation ID.
            - customer_id (str, optional): UUID of the customer if known.

    Returns:
        Ticket ID and confirmation message.
    """
    try:
        raw = json.loads(escalation_json)
        request = EscalationRequest.model_validate(raw)
    except (json.JSONDecodeError, ValidationError) as exc:
        return f"Invalid escalation request: {exc}"

    ticket_id = uuid.uuid4()

    try:
        import uuid as uuid_module

        customer_uuid = None
        if request.customer_id:
            try:
                customer_uuid = uuid_module.UUID(request.customer_id)
            except ValueError:
                customer_uuid = None

        async with AsyncSessionLocal() as session:
            ticket = SupportTicket(
                id=ticket_id,
                customer_id=customer_uuid,
                conversation_id=request.conversation_id or "unknown",
                subject=f"Escalation: {request.reason[:200]}",
                description=request.summary,
                priority=request.priority,
                status="open",
            )
            session.add(ticket)
            await session.commit()

        return (
            f"Escalation successful. A support ticket has been created.\n"
            f"Ticket ID : {ticket_id}\n"
            f"Priority  : {request.priority}\n"
            f"Reason    : {request.reason}\n"
            "A human agent will review this conversation and contact the customer shortly."
        )

    except Exception as exc:
        logger.exception("escalate_to_human failed: %s", exc)
        return (
            f"Escalation ticket could not be persisted due to an error ({exc}), "
            f"but the escalation has been recorded with reference ID {ticket_id}. "
            "Please notify a human agent manually."
        )
