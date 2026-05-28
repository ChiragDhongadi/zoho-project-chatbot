from typing import Literal
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from backend.app.config import settings
from backend.app.agents.state import AgentState

from backend.app.agents.query_agent import query_agent_node
from backend.app.agents.action_agent import action_agent_node

# SUPERVISOR / ROUTER LLM SETUP

router_model = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model=settings.GROQ_MODEL,
    temperature=0.0
)

ROUTER_SYSTEM_PROMPT = """You are the Supervisor/Router for the AI-Powered Zoho Projects Chatbot.
Your job is to analyze the user's latest message and classify it into one of these categories:
1. "query_agent": If the user wants to READ, fetch, list, count, or summarize information (e.g. view projects, list tasks, show members, calculate utilization, or check status).
2. "action_agent": If the user wants to WRITE, create, edit, update, assign, or delete something (e.g. make a task, delete a task, change due date, set assignee).
3. "general": If the user is just saying hi, hello, thanking you, asking general questions about who you are, or making small talk.

Your output MUST be exactly one of these three strings: "query_agent", "action_agent", or "general". Do not write any other words, markdown, or punctuation."""

# WORKFLOW NODES

async def router_node(state: AgentState) -> dict:
    """
    Supervisor entrypoint node.
    If the input is just general conversation (greeting, thanks), 
    it generates a friendly response directly using Groq to save routing cycles.
    """
    print("[Graph Node] Supervisor/Router entrypoint invoked.")
    
    if state.get("pending_action"):
        return {"messages": []}

    messages = state.get("messages", [])
    if not messages:
        return {"messages": []}
        
    last_msg = messages[-1].content
    
    classification_response = await router_model.ainvoke([
        SystemMessage(content=ROUTER_SYSTEM_PROMPT),
        HumanMessage(content=last_msg)
    ])
    
    decision = classification_response.content.strip().lower()
    print(f"[Graph Router] Routing decision classification: {decision}")

    if "general" in decision:
        chat_prompt = [
            SystemMessage(content="You are a friendly, professional AI Assistant for Zoho Projects. Greet the user warmly, answer their general small talk, or guide them to ask you about listing/creating tasks on their Zoho projects. Keep your answer brief and premium."),
            HumanMessage(content=last_msg)
        ]
        chat_response = await router_model.ainvoke(chat_prompt)
        return {"messages": [chat_response]}

    return {"messages": []}

# ROUTING EDGE DECISION

async def route_decision(state: AgentState) -> Literal["query_agent", "action_agent", "__end__"]:
    """
    Asynchronous conditional routing logic.
    Directs graph flow to Query Agent, Action Agent, or exits.
    """
    if state.get("pending_action"):
        print("[Graph Route Edge] Active pending action found. Routing directly to Action Agent.")
        return "action_agent"

    messages = state.get("messages", [])
    if not messages:
        return "__end__"
        
    last_msg = messages[-1].content
    
    if len(messages) >= 2 and isinstance(messages[-1], AIMessage) and not messages[-1].tool_calls:
        if "general" in last_msg.lower() or any(w in last_msg.lower() for w in ["hi", "hello", "thanks"]):
            return "__end__"

    try:
        classification_response = await router_model.ainvoke([
            SystemMessage(content=ROUTER_SYSTEM_PROMPT),
            HumanMessage(content=last_msg)
        ])
        decision = classification_response.content.strip().lower()
        
        if "action" in decision:
            return "action_agent"
        elif "query" in decision:
            return "query_agent"
        else:
            return "__end__"

    except Exception as e:
        print(f"[Graph Route Edge] Router error {str(e)}. Using fallback regex...")
        last_msg_lower = last_msg.lower()
        if any(kw in last_msg_lower for kw in ["create", "delete", "update", "add", "change", "assign"]):
            return "action_agent"
        return "query_agent"

# ASSEMBLE GRAPH TOPOLOGY

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
print("Stateful Multi-Agent LangGraph compiled successfully!")
