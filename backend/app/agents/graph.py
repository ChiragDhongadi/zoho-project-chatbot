from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from backend.app.agents.state import AgentState

# NODES

async def router_node(state: AgentState) -> dict:
    """Supervisor/Router node that determines where to direct the query."""
    print("[Graph Node] Supervisor/Router invoked.")
    return {"messages": []}

async def query_agent_node(state: AgentState) -> dict:
    """Query Agent Node - Handles Read requests (projects, tasks, members)."""
    print("[Graph Node] Query Agent invoked.")
    return {"messages": []}

async def action_agent_node(state: AgentState) -> dict:
    """Action Agent Node - Handles Write requests (create, update, delete)."""
    print("[Graph Node] Action Agent invoked.")
    return {"messages": []}


# ROUTING LOGIC

def route_decision(state: AgentState) -> Literal["query_agent", "action_agent", "__end__"]:
    """Conditional router that directs graph execution to the correct agent node."""

    last_message = state["messages"][-1].content.lower() if state["messages"] else ""
    
    if "create" in last_message or "delete" in last_message or "update" in last_message:
        return "action_agent"
    elif "project" in last_message or "task" in last_message or "member" in last_message:
        return "query_agent"
    return "__end__"


# BUILDING THE GRAPH

builder = StateGraph(AgentState)

builder.add_node("router", router_node)
builder.add_node("query_agent", query_agent_node)
builder.add_node("action_agent", action_agent_node)


builder.set_entry_point("router")

builder.add_conditional_edges(
    "router",
    route_decision,
    {
        "query_agent": "query_agent",
        "action_agent": "action_agent",
        "__end__": END
    }
)

builder.add_edge("query_agent", END)
builder.add_edge("action_agent", END)

memory_checkpointer = MemorySaver()

compiled_graph = builder.compile(
    checkpointer=memory_checkpointer
)
print("Skeletal LangGraph workflow compiled successfully!")
