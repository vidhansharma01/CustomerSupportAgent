# Import all models here so that Alembic (and init_db) can discover them
# via Base.metadata.

from backend.models.customer import Customer, Order  # noqa: F401
from backend.models.document import Document  # noqa: F401
from backend.models.ticket import ConversationMessage, SupportTicket  # noqa: F401

__all__ = [
    "Customer",
    "Order",
    "Document",
    "SupportTicket",
    "ConversationMessage",
]
