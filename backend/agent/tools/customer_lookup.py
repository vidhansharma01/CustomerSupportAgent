from __future__ import annotations

import logging
from uuid import UUID

from langchain_core.tools import tool
from sqlalchemy import select

from backend.database import AsyncSessionLocal
from backend.models.customer import Customer, Order

logger = logging.getLogger(__name__)


@tool
async def lookup_customer(identifier: str) -> str:
    """Look up customer information including account status, tier, and recent orders.

    Args:
        identifier: Either a UUID customer ID or an email address.

    Returns:
        Formatted string with customer details and last 5 orders.
    """
    try:
        async with AsyncSessionLocal() as session:
            # Try UUID first, fall back to email lookup
            customer: Customer | None = None
            try:
                customer_uuid = UUID(identifier)
                result = await session.execute(
                    select(Customer).where(Customer.id == customer_uuid)
                )
                customer = result.scalar_one_or_none()
            except ValueError:
                # Not a UUID — treat as email
                result = await session.execute(
                    select(Customer).where(Customer.email == identifier.lower().strip())
                )
                customer = result.scalar_one_or_none()

            if customer is None:
                return f"No customer found with identifier: {identifier}"

            # Fetch last 5 orders
            orders_result = await session.execute(
                select(Order)
                .where(Order.customer_id == customer.id)
                .order_by(Order.created_at.desc())
                .limit(5)
            )
            orders = orders_result.scalars().all()

        lines = [
            "=== Customer Information ===",
            f"Name       : {customer.name}",
            f"Email      : {customer.email}",
            f"Phone      : {customer.phone or 'N/A'}",
            f"Tier       : {customer.tier}",
            f"Status     : {customer.account_status}",
            f"Member Since: {customer.created_at.strftime('%Y-%m-%d')}",
        ]

        if orders:
            lines.append("\n--- Recent Orders (last 5) ---")
            for order in orders:
                lines.append(
                    f"  Order #{order.order_number} | {order.status} | "
                    f"${order.total_amount} | {order.created_at.strftime('%Y-%m-%d')}"
                )
        else:
            lines.append("\nNo orders found for this customer.")

        return "\n".join(lines)

    except Exception as exc:
        logger.exception("lookup_customer failed: %s", exc)
        return f"Customer lookup encountered an error: {exc}"
