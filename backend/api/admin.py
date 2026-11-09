from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.customer import Customer
from backend.models.ticket import SupportTicket
from backend.schemas.customer import CustomerRead
from backend.schemas.ticket import TicketRead, TicketUpdate

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ---------------------------------------------------------------------------
# Tickets
# ---------------------------------------------------------------------------


@router.get("/tickets", response_model=list[TicketRead])
async def list_tickets(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> list[SupportTicket]:
    """List all support tickets (paginated)."""
    result = await db.execute(
        select(SupportTicket)
        .order_by(SupportTicket.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


@router.get("/tickets/{ticket_id}", response_model=TicketRead)
async def get_ticket(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> SupportTicket:
    """Retrieve a single support ticket by ID."""
    result = await db.execute(
        select(SupportTicket).where(SupportTicket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    return ticket


@router.patch("/tickets/{ticket_id}", response_model=TicketRead)
async def update_ticket(
    ticket_id: uuid.UUID,
    payload: TicketUpdate,
    db: AsyncSession = Depends(get_db),
) -> SupportTicket:
    """Update a ticket's status, priority, assignment, or resolved_at timestamp."""
    result = await db.execute(
        select(SupportTicket).where(SupportTicket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found.")

    update_data = payload.model_dump(exclude_none=True)

    # Auto-set resolved_at when status moves to resolved/closed
    if "status" in update_data and update_data["status"] in ("resolved", "closed"):
        if ticket.resolved_at is None:
            ticket.resolved_at = datetime.now(tz=timezone.utc)

    for field, value in update_data.items():
        setattr(ticket, field, value)

    await db.commit()
    await db.refresh(ticket)
    return ticket


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------


@router.get("/customers", response_model=list[CustomerRead])
async def list_customers(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> list[Customer]:
    """List all customers (paginated)."""
    result = await db.execute(
        select(Customer)
        .order_by(Customer.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())
