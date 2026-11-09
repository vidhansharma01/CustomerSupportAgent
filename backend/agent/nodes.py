from __future__ import annotations

import logging

from langchain_core.messages import AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode

from backend.agent.state import AgentState
from backend.agent.tools.action_executor import execute_customer_action
from backend.agent.tools.customer_lookup import lookup_customer
from backend.agent.tools.escalate import escalate_to_human
from backend.agent.tools.kb_search import search_knowledge_base
from backend.config import settings

logger = logging.getLogger(__name__)

TOOLS = [
    search_knowledge_base,
    lookup_customer,
    execute_customer_action,
    escalate_to_human,
]

SYSTEM_PROMPT = """You are a helpful, professional customer support agent for our company.

## Your Role
You assist customers with questions about their orders, account information, company policies,
product details, and common issues. You have access to our knowledge base, customer database,
and a set of approved actions you can take on behalf of customers.

## Available Tools
- **search_knowledge_base**: Find relevant policies, FAQs, product information, and procedures.
- **lookup_customer**: Retrieve customer account details and order history.
- **execute_customer_action**: Perform approved actions such as:
  - update_email / update_phone
  - request_refund (up to ${refund_limit} without further approval)
  - cancel_order
  - resend_invoice
- **escalate_to_human**: Hand off to a human agent when needed.

## Escalation Criteria
Escalate immediately if:
- The customer requests a refund exceeding ${refund_limit}.
- The customer uses abusive language or is extremely distressed.
- The issue involves legal, compliance, or fraud concerns.
- You have attempted to resolve the issue {max_iterations} times without success.
- The customer explicitly asks to speak with a human.

## Tone & Guidelines
- Be empathetic, concise, and professional at all times.
- Always confirm actions before executing them when possible.
- Cite the relevant policy or document when providing policy-related answers.
- Never fabricate information — if unsure, search the knowledge base first.
- Protect customer privacy; do not reveal other customers' data.
""".format(
    refund_limit=settings.refund_limit_usd,
    max_iterations=settings.max_iterations,
)

_llm = ChatOpenAI(
    model=settings.openai_model,
    api_key=settings.openai_api_key,
    temperature=0,
    streaming=True,
).bind_tools(TOOLS)

_tool_node = ToolNode(TOOLS)


async def call_llm(state: AgentState) -> dict:
    """Invoke the LLM with bound tools and return updated messages."""
    messages = state["messages"]

    # Prepend system prompt if first turn
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)

    response: AIMessage = await _llm.ainvoke(messages)
    logger.debug("LLM response: %s", response)
    return {"messages": [response]}


def route_after_llm(state: AgentState) -> str:
    """Decide next node after LLM response."""
    messages = state["messages"]
    tool_call_count = state.get("tool_call_count", 0)

    if tool_call_count >= settings.escalation_threshold:
        logger.warning(
            "Tool call count %d exceeded escalation threshold %d — forcing escalation.",
            tool_call_count,
            settings.escalation_threshold,
        )
        return "escalate"

    last_message = messages[-1] if messages else None
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"

    return "end"


async def run_tools(state: AgentState) -> dict:
    """Execute tool calls found in the last AI message."""
    result = await _tool_node.ainvoke(state)
    new_count = state.get("tool_call_count", 0) + 1
    result["tool_call_count"] = new_count
    return result


async def handle_escalation(state: AgentState) -> dict:
    """Force-escalate the conversation when the threshold is exceeded."""
    import json
    import uuid

    conversation_id = state.get("conversation_id", "unknown")
    customer_id = state.get("customer_id")

    # Build a summary from the last few messages
    recent = state["messages"][-6:]
    summary_lines = []
    for m in recent:
        role = getattr(m, "type", "unknown")
        content = m.content if isinstance(m.content, str) else str(m.content)
        summary_lines.append(f"{role}: {content[:200]}")
    summary = "\n".join(summary_lines) or "No conversation summary available."

    escalation_payload = json.dumps(
        {
            "reason": "Maximum tool-call iterations reached without resolution.",
            "priority": "high",
            "summary": summary,
            "conversation_id": conversation_id,
            "customer_id": customer_id,
        }
    )

    escalation_result = await escalate_to_human.ainvoke(escalation_payload)
    ticket_id = None

    # Extract ticket ID from result message
    for line in escalation_result.splitlines():
        if line.startswith("Ticket ID"):
            parts = line.split(":")
            if len(parts) == 2:
                ticket_id = parts[1].strip()

    from langchain_core.messages import AIMessage

    return {
        "escalated": True,
        "ticket_id": ticket_id,
        "messages": [
            AIMessage(
                content=(
                    "I've escalated your case to a human support agent who will "
                    "follow up with you shortly. " + escalation_result
                )
            )
        ],
    }
