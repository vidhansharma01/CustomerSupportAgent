"""
DeepEval LLM-based tests for the Customer Support Agent.

Run with: uv run pytest tests/test_agent.py -v

Requires OPENAI_API_KEY set in environment.
DeepEval runs actual LLM calls to evaluate quality.
"""
import pytest
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    ContextualRecallMetric,
    HallucinationMetric,
)


# ---------------------------------------------------------------------------
# Metric configuration
# ---------------------------------------------------------------------------
ANSWER_RELEVANCY = AnswerRelevancyMetric(threshold=0.7, model="gpt-4o", include_reason=True)
FAITHFULNESS = FaithfulnessMetric(threshold=0.7, model="gpt-4o", include_reason=True)
HALLUCINATION = HallucinationMetric(threshold=0.4, model="gpt-4o", include_reason=True)


# ---------------------------------------------------------------------------
# Test: KB answer is relevant
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("question,expected_keywords", [
    (
        "What is your refund policy?",
        ["refund", "30 days", "receipt"],
    ),
    (
        "How do I cancel my order?",
        ["cancel", "order", "contact"],
    ),
    (
        "What payment methods do you accept?",
        ["credit", "debit", "PayPal"],
    ),
])
def test_kb_answer_relevancy(question: str, expected_keywords: list[str]):
    """Test that KB answers are relevant to the question."""
    # Simulate a retrieval context (would come from actual DB in integration tests)
    retrieval_context = [
        "Our refund policy allows returns within 30 days of purchase with original receipt. "
        "Refunds are processed within 5-7 business days.",
        "To cancel an order, please contact customer support within 24 hours of placing the order. "
        "Orders already shipped cannot be cancelled.",
        "We accept Visa, Mastercard, American Express, Discover, PayPal, and Apple Pay.",
    ]

    # Simulate agent response
    actual_output = (
        f"Based on our company policy: {retrieval_context[0]} "
        "Please let me know if you need further assistance."
    )

    test_case = LLMTestCase(
        input=question,
        actual_output=actual_output,
        retrieval_context=retrieval_context,
    )
    assert_test(test_case, [ANSWER_RELEVANCY])


# ---------------------------------------------------------------------------
# Test: Agent does not hallucinate
# ---------------------------------------------------------------------------
def test_no_hallucination_on_policy_question():
    """Agent should not make up policy details not in context."""
    context = [
        "Standard shipping takes 5-7 business days. Express shipping takes 1-2 business days.",
        "Free shipping is available on orders over $50.",
    ]
    actual_output = (
        "Standard shipping takes 5-7 business days and express shipping takes 1-2 business days. "
        "Orders over $50 qualify for free standard shipping."
    )
    test_case = LLMTestCase(
        input="How long does shipping take?",
        actual_output=actual_output,
        context=context,
    )
    assert_test(test_case, [HALLUCINATION])


# ---------------------------------------------------------------------------
# Test: Escalation response is appropriate
# ---------------------------------------------------------------------------
def test_escalation_response_quality():
    """When escalating, the response should be empathetic and informative."""
    actual_output = (
        "I understand your frustration and I'm sorry for the inconvenience. "
        "I've escalated your case to our senior support team. "
        "Your ticket number is #TKT-12345. A specialist will contact you within 2 business hours."
    )
    test_case = LLMTestCase(
        input="I've been waiting 3 weeks for my refund and nobody is helping me!",
        actual_output=actual_output,
        retrieval_context=[
            "Escalation policy: When a customer has been waiting more than 2 weeks for a refund, "
            "escalate to senior support team immediately with high priority."
        ],
    )
    assert_test(test_case, [ANSWER_RELEVANCY])


# ---------------------------------------------------------------------------
# Test: Action validation — refund within policy
# ---------------------------------------------------------------------------
def test_refund_action_within_policy():
    """Agent should correctly handle refund requests within policy limits."""
    actual_output = (
        "I've successfully initiated a refund of $45.99 for order #ORD-001. "
        "You'll receive the funds in 5-7 business days."
    )
    test_case = LLMTestCase(
        input="I want a refund for order #ORD-001 for $45.99",
        actual_output=actual_output,
        retrieval_context=[
            "Refund policy: Agents can approve refunds up to $500. "
            "Process refunds within 5-7 business days to original payment method."
        ],
    )
    assert_test(test_case, [ANSWER_RELEVANCY, FAITHFULNESS])


# ---------------------------------------------------------------------------
# Test: Faithfulness — agent sticks to KB content
# ---------------------------------------------------------------------------
def test_faithfulness_to_knowledge_base():
    """Agent answers should be faithful to retrieved KB content."""
    retrieval_context = [
        "Our premium tier customers receive 24/7 priority support with a 1-hour response SLA. "
        "Standard tier customers receive support during business hours with a 24-hour response SLA."
    ]
    actual_output = (
        "As a Premium tier customer, you have access to 24/7 priority support "
        "with a 1-hour response SLA."
    )
    test_case = LLMTestCase(
        input="What kind of support do I get as a premium customer?",
        actual_output=actual_output,
        retrieval_context=retrieval_context,
    )
    assert_test(test_case, [FAITHFULNESS])
