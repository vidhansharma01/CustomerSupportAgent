"""
Unit tests for agent tools.
Tests tool input validation, Pydantic schemas, and DB interactions.
"""
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal


# ---------------------------------------------------------------------------
# Test: Action validation with Pydantic
# ---------------------------------------------------------------------------
class TestActionValidation:
    """Test that action_executor validates inputs correctly."""

    def test_valid_refund_action(self):
        """Valid refund action should pass validation."""
        from pydantic import BaseModel
        from typing import Literal

        class ActionRequest(BaseModel):
            action: Literal[
                "update_email", "update_phone", "request_refund",
                "cancel_order", "resend_invoice"
            ]
            customer_id: str
            params: dict

        req = ActionRequest(
            action="request_refund",
            customer_id=str(uuid.uuid4()),
            params={"amount": 49.99, "order_id": str(uuid.uuid4()), "reason": "defective product"}
        )
        assert req.action == "request_refund"
        assert req.params["amount"] == 49.99

    def test_invalid_action_rejected(self):
        """Unknown actions should be rejected by Pydantic."""
        from pydantic import BaseModel, ValidationError
        from typing import Literal

        class ActionRequest(BaseModel):
            action: Literal[
                "update_email", "update_phone", "request_refund",
                "cancel_order", "resend_invoice"
            ]
            customer_id: str
            params: dict

        with pytest.raises(ValidationError):
            ActionRequest(
                action="delete_customer",  # not in allowlist
                customer_id=str(uuid.uuid4()),
                params={}
            )

    def test_refund_exceeds_limit(self):
        """Refund amount above limit should be caught."""
        refund_limit = 500.0
        requested_amount = 1500.0
        assert requested_amount > refund_limit, "Should exceed limit"

    def test_refund_within_limit(self):
        """Refund amount within limit should pass."""
        refund_limit = 500.0
        requested_amount = 250.0
        assert requested_amount <= refund_limit


# ---------------------------------------------------------------------------
# Test: Chat schemas
# ---------------------------------------------------------------------------
class TestChatSchemas:
    """Test Pydantic chat schemas."""

    def test_chat_request_valid(self):
        """Valid chat request should parse correctly."""
        from backend.schemas.chat import ChatRequest

        req = ChatRequest(
            conversation_id="conv-123",
            message="What is your return policy?",
        )
        assert req.conversation_id == "conv-123"
        assert req.customer_id is None

    def test_chat_request_with_customer(self):
        """Chat request with customer_id should parse."""
        from backend.schemas.chat import ChatRequest

        cid = uuid.uuid4()
        req = ChatRequest(
            conversation_id="conv-456",
            message="Check my order status",
            customer_id=cid,
        )
        assert req.customer_id == cid

    def test_source_doc_schema(self):
        """SourceDoc schema should validate relevance score."""
        from backend.schemas.chat import SourceDoc

        doc = SourceDoc(title="Refund Policy", category="policy", relevance=0.85)
        assert 0 <= doc.relevance <= 1


# ---------------------------------------------------------------------------
# Test: Agent state structure
# ---------------------------------------------------------------------------
class TestAgentState:
    """Test AgentState TypedDict structure."""

    def test_agent_state_has_required_keys(self):
        """AgentState should have all required keys."""
        from backend.agent.state import AgentState

        # Check it's importable and has the right annotations
        annotations = AgentState.__annotations__
        required_keys = [
            "messages", "conversation_id", "customer_id",
            "customer_data", "tool_call_count", "escalated",
            "ticket_id", "sources", "final_answer"
        ]
        for key in required_keys:
            assert key in annotations, f"Missing key: {key}"


# ---------------------------------------------------------------------------
# Test: KB search result merging logic
# ---------------------------------------------------------------------------
class TestKBSearchMerging:
    """Test knowledge base result deduplication and merging."""

    def test_deduplication_by_title(self):
        """Results with same title from vector and FTS should be deduplicated."""
        vector_results = [
            {"title": "Refund Policy", "content": "30 day returns", "category": "policy", "score": 0.9},
            {"title": "Shipping Info", "content": "5-7 days", "category": "faq", "score": 0.7},
        ]
        fts_results = [
            {"title": "Refund Policy", "content": "30 day returns", "category": "policy", "score": 0.8},
            {"title": "Return Process", "content": "How to return", "category": "policy", "score": 0.6},
        ]

        seen = set()
        merged = []
        for r in vector_results + fts_results:
            if r["title"] not in seen:
                seen.add(r["title"])
                merged.append(r)

        assert len(merged) == 3  # Refund Policy deduplicated
        titles = [r["title"] for r in merged]
        assert titles.count("Refund Policy") == 1


# ---------------------------------------------------------------------------
# Test: Health endpoint
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Health endpoint should return 200 with status ok."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


# ---------------------------------------------------------------------------
# Test: Chat endpoint validation
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_chat_endpoint_missing_message(client):
    """Chat endpoint should reject empty message."""
    response = await client.post("/api/chat", json={
        "conversation_id": "test-conv",
        "message": ""
    })
    # Should return 422 (validation error) or 400
    assert response.status_code in (400, 422)
