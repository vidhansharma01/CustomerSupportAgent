from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID
    order_number: str
    status: str
    total_amount: Decimal
    created_at: datetime


class CustomerBase(BaseModel):
    email: str
    name: str
    phone: Optional[str] = None
    account_status: str = "active"
    tier: str = "standard"


class CustomerCreate(CustomerBase):
    pass


class CustomerRead(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    orders: list[OrderRead] = []


class CustomerUpdate(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    account_status: Optional[str] = None
    tier: Optional[str] = None
