from __future__ import annotations

import logging

from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from backend.agent.nodes import call_llm, handle_escalation, route_after_llm, run_tools
from backend.agent.state import AgentState

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

_builder = StateGraph(AgentState)

_builder.add_node("llm", call_llm)
_builder.add_node("tools", run_tools)
_builder.add_node("escalate", handle_escalation)

# Edges
_builder.add_edge(START, "llm")
_builder.add_conditional_edges(
    "llm",
    route_after_llm,
    {
        "tools": "tools",
        "escalate": "escalate",
        "end": END,
    },
)
_builder.add_edge("tools", "llm")
_builder.add_edge("escalate", END)

# Compile with an in-memory checkpointer (supports multi-turn conversations)
_checkpointer = MemorySaver()
agent_graph = _builder.compile(checkpointer=_checkpointer)


# ---------------------------------------------------------------------------
# Public helper
# ---------------------------------------------------------------------------


async def run_agent(state_input: dict, config: dict) -> AgentState:
    """Run the compiled agent graph and return the final state.

    Args:
        state_input: Initial AgentState fields (must include 'messages' and 'conversation_id').
        config: LangGraph RunnableConfig (should include {'configurable': {'thread_id': ...}}).

    Returns:
        Final AgentState after the graph finishes.
    """
    final_state: AgentState = await agent_graph.ainvoke(state_input, config=config)

    # Collect sources from messages that mention knowledge base results
    sources: list[dict] = []
    for msg in final_state.get("messages", []):
        if hasattr(msg, "content") and "Knowledge Base Results" in str(msg.content):
            # Already aggregated in state; sources populated by kb_search if needed
            pass

    final_state.setdefault("sources", sources)

    # Capture final assistant answer
    messages = final_state.get("messages", [])
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            final_state["final_answer"] = str(msg.content)
            break

    return final_state
