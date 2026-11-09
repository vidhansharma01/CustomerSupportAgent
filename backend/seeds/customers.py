"""Seed script: creates 5 sample customers + 10 sample orders.

Run with:
    uv run python -m backend.seeds.customers
"""
from __future__ import annotations

import asyncio
import uuid
from decimal import Decimal

from backend.database import AsyncSessionLocal, init_db
from backend.models.customer import Customer, Order


SAMPLE_CUSTOMERS: list[dict] = [
    {
        "id": uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001"),
        "email": "alice.johnson@example.com",
        "name": "Alice Johnson",
        "phone": "+1-555-0101",
        "account_status": "active",
        "tier": "premium",
    },
    {
        "id": uuid.UUID("aaaaaaaa-0000-0000-0000-000000000002"),
        "email": "bob.smith@example.com",
        "name": "Bob Smith",
        "phone": "+1-555-0102",
        "account_status": "active",
        "tier": "standard",
    },
    {
        "id": uuid.UUID("aaaaaaaa-0000-0000-0000-000000000003"),
        "email": "carol.white@example.com",
        "name": "Carol White",
        "phone": None,
        "account_status": "active",
        "tier": "enterprise",
    },
    {
        "id": uuid.UUID("aaaaaaaa-0000-0000-0000-000000000004"),
        "email": "david.brown@example.com",
        "name": "David Brown",
        "phone": "+1-555-0104",
        "account_status": "suspended",
        "tier": "standard",
    },
    {
        "id": uuid.UUID("aaaaaaaa-0000-0000-0000-000000000005"),
        "email": "eve.davis@example.com",
        "name": "Eve Davis",
        "phone": "+1-555-0105",
        "account_status": "active",
        "tier": "premium",
    },
]

SAMPLE_ORDERS: list[dict] = [
    # Alice – 3 orders
    {
        "id": uuid.uuid4(),
        "customer_id": uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001"),
        "order_number": "ORD-10001",
        "status": "delivered",
        "total_amount": Decimal("129.99"),
    },
    {
        "id": uuid.uuid4(),
        "customer_id": uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001"),
        "order_number": "ORD-10002",
        "status": "shipped",
        "total_amount": Decimal("49.99"),
    },
    {
        "id": uuid.uuid4(),
        "customer_id": uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001"),
        "order_number": "ORD-10003",
        "status": "processing",
        "total_amount": Decimal("299.00"),
    },
    # Bob – 2 orders
    {
        "id": uuid.uuid4(),
        "customer_id": uuid.UUID("aaaaaaaa-0000-0000-0000-000000000002"),
        "order_number": "ORD-10004",
        "status": "delivered",
        "total_amount": Decimal("75.50"),
    },
    {
        "id": uuid.uuid4(),
        "customer_id": uuid.UUID("aaaaaaaa-0000-0000-0000-000000000002"),
        "order_number": "ORD-10005",
        "status": "cancelled",
        "total_amount": Decimal("19.99"),
    },
    # Carol – 2 orders
    {
        "id": uuid.uuid4(),
        "customer_id": uuid.UUID("aaaaaaaa-0000-0000-0000-000000000003"),
        "order_number": "ORD-10006",
        "status": "delivered",
        "total_amount": Decimal("1250.00"),
    },
    {
        "id": uuid.uuid4(),
        "customer_id": uuid.UUID("aaaaaaaa-0000-0000-0000-000000000003"),
        "order_number": "ORD-10007",
        "status": "pending",
        "total_amount": Decimal("430.00"),
    },
    # David – 1 order
    {
        "id": uuid.uuid4(),
        "customer_id": uuid.UUID("aaaaaaaa-0000-0000-0000-000000000004"),
        "order_number": "ORD-10008",
        "status": "delivered",
        "total_amount": Decimal("34.99"),
    },
    # Eve – 2 orders
    {
        "id": uuid.uuid4(),
        "customer_id": uuid.UUID("aaaaaaaa-0000-0000-0000-000000000005"),
        "order_number": "ORD-10009",
        "status": "shipped",
        "total_amount": Decimal("89.95"),
    },
    {
        "id": uuid.uuid4(),
        "customer_id": uuid.UUID("aaaaaaaa-0000-0000-0000-000000000005"),
        "order_number": "ORD-10010",
        "status": "delivered",
        "total_amount": Decimal("199.99"),
    },
]


async def seed() -> None:
    await init_db()

    async with AsyncSessionLocal() as session:
        # Customers
        for cdata in SAMPLE_CUSTOMERS:
            existing = await session.get(Customer, cdata["id"])
            if existing is None:
                session.add(Customer(**cdata))
                print(f"  + Customer: {cdata['name']} ({cdata['email']})")
            else:
                print(f"  ~ Customer already exists: {cdata['email']}")

        await session.flush()

        # Orders
        for odata in SAMPLE_ORDERS:
            session.add(Order(**odata))
            print(f"  + Order: {odata['order_number']} [{odata['status']}]")

        await session.commit()

    print("\n✅ Customer & order seeding complete.")


if __name__ == "__main__":
    asyncio.run(seed())
