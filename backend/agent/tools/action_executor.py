from __future__ import annotations

import json
import logging
from typing import Literal
from uuid import UUID

from langchain_core.tools import tool
from pydantic import BaseModel, ValidationError
from sqlalchemy import select

from backend.config import settings
from backend.database import AsyncSessionLocal
from backend.models.customer import Customer, Order

logger = logging.getLogger(__name__)


class ActionRequest(BaseModel):
    action: Literal[
        "update_email",
        "update_phone",
        "request_refund",
        "cancel_order",
        "resend_invoice",
    ]
    customer_id: str
    params: dict


@tool
async def execute_customer_action(action_json: str) -> str:
    """Execute an approved action for a customer.

    Available actions: update_email, update_phone, request_refund, cancel_order, resend_invoice.

    Args:
        action_json: JSON string with keys: action (str), customer_id (str), params (dict).
            - update_email: params = {"new_email": "..."}
            - update_phone: params = {"new_phone": "..."}
            - request_refund: params = {"amount": float, "order_number": "...", "reason": "..."}
            - cancel_order: params = {"order_number": "..."}
            - resend_invoice: params = {"order_number": "..."}

    Returns:
        Success or failure message describing the outcome.
    """
    try:
        raw = json.loads(action_json)
        request = ActionRequest.model_validate(raw)
    except (json.JSONDecodeError, ValidationError) as exc:
        return f"Invalid action request: {exc}"

    try:
        customer_uuid = UUID(request.customer_id)
    except ValueError:
        return f"Invalid customer_id format: {request.customer_id}"

    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(Customer).where(Customer.id == customer_uuid)
            )
            customer = result.scalar_one_or_none()
            if customer is None:
                return f"Customer {request.customer_id} not found."

            action = request.action
            params = request.params

            # ------------------------------------------------------------------ #
            #  update_email
            # ------------------------------------------------------------------ #
            if action == "update_email":
                new_email = params.get("new_email", "").strip().lower()
                if not new_email:
                    return "Missing 'new_email' in params."
                old_email = customer.email
                customer.email = new_email
                await session.commit()
                return f"Email updated from {old_email} to {new_email} for customer {customer.name}."

            # ------------------------------------------------------------------ #
            #  update_phone
            # ------------------------------------------------------------------ #
            elif action == "update_phone":
                new_phone = params.get("new_phone", "").strip()
                if not new_phone:
                    return "Missing 'new_phone' in params."
                customer.phone = new_phone
                await session.commit()
                return f"Phone updated to {new_phone} for customer {customer.name}."

            # ------------------------------------------------------------------ #
            #  request_refund
            # ------------------------------------------------------------------ #
            elif action == "request_refund":
                amount = params.get("amount")
                order_number = params.get("order_number", "")
                reason = params.get("reason", "No reason provided")

                if amount is None:
                    return "Missing 'amount' in params."
                try:
                    amount = float(amount)
                except (TypeError, ValueError):
                    return "Invalid 'amount' value — must be a number."

                if amount > settings.refund_limit_usd:
                    return (
                        f"Refund amount ${amount:.2f} exceeds the agent limit of "
                        f"${settings.refund_limit_usd:.2f}. "
                        "Please escalate to a human agent for approval."
                    )
                if amount <= 0:
                    return "Refund amount must be greater than zero."

                # Verify the order belongs to the customer
                if order_number:
                    order_result = await session.execute(
                        select(Order).where(
                            Order.order_number == order_number,
                            Order.customer_id == customer_uuid,
                        )
                    )
                    order = order_result.scalar_one_or_none()
                    if order is None:
                        return f"Order #{order_number} not found for this customer."
                    order_info = f" for order #{order_number}"
                else:
                    order_info = ""

                return (
                    f"Refund of ${amount:.2f}{order_info} approved for {customer.name}. "
                    f"Reason: {reason}. "
                    "The refund will be processed within 3–5 business days."
                )

            # ------------------------------------------------------------------ #
            #  cancel_order
            # ------------------------------------------------------------------ #
            elif action == "cancel_order":
                order_number = params.get("order_number", "")
                if not order_number:
                    return "Missing 'order_number' in params."

                order_result = await session.execute(
                    select(Order).where(
                        Order.order_number == order_number,
                        Order.customer_id == customer_uuid,
                    )
                )
                order = order_result.scalar_one_or_none()
                if order is None:
                    return f"Order #{order_number} not found for customer {customer.name}."

                if order.status in ("delivered", "cancelled"):
                    return (
                        f"Order #{order_number} cannot be cancelled — "
                        f"current status is '{order.status}'."
                    )

                order.status = "cancelled"
                await session.commit()
                return (
                    f"Order #{order_number} has been successfully cancelled "
                    f"for {customer.name}."
                )

            # ------------------------------------------------------------------ #
            #  resend_invoice
            # ------------------------------------------------------------------ #
            elif action == "resend_invoice":
                order_number = params.get("order_number", "")
                if not order_number:
                    return "Missing 'order_number' in params."

                order_result = await session.execute(
                    select(Order).where(
                        Order.order_number == order_number,
                        Order.customer_id == customer_uuid,
                    )
                )
                order = order_result.scalar_one_or_none()
                if order is None:
                    return f"Order #{order_number} not found for customer {customer.name}."

                # In a real system this would trigger an email service
                return (
                    f"Invoice for order #{order_number} has been resent to "
                    f"{customer.email}."
                )

            else:
                return f"Unknown action: {action}"

        except Exception as exc:
            await session.rollback()
            logger.exception("execute_customer_action DB error: %s", exc)
            return f"Database error while executing action: {exc}"
