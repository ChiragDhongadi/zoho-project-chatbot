from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, ToolMessage, AIMessage
from backend.app.config import settings
from backend.app.agents.state import AgentState
from backend.app.agents.tools import (
    list_projects,
    list_tasks,
    get_task_details,
    list_project_members,
    get_task_utilisation
)

model = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model=settings.GROQ_MODEL,
    temperature=0.0
)

READ_TOOLS = {
    "list_projects": list_projects,
    "list_tasks": list_tasks,
    "get_task_details": get_task_details,
    "list_project_members": list_project_members,
    "get_task_utilisation": get_task_utilisation
}

query_agent_llm = model.bind_tools(list(READ_TOOLS.values()))

SYSTEM_PROMPT = """You are the specialized Query Agent for Zoho Projects.
Your sole responsibility is to answer READ-ONLY queries (fetching, listing, describing, or summarizing projects, tasks, members, and utilization).

RULES:
1. You are strictly READ-ONLY. You MUST NOT attempt to create, update, assign, or delete anything.
2. If the user asks you to perform a write operation (e.g., "create task", "delete task"), politely tell them:
   "I am the Query Agent and can only look up information. Please let me redirect you to the Action Agent to execute this request."
   Then do not make any tool calls.
3. If the user's message is ambiguous, use your tools to look up the necessary information.
4. Short-term Memory Context: Pay close attention to previous messages. If a user asks "show tasks for the first one", refer to the project list retrieved earlier, find the first project's ID, and call list_tasks with that project ID.
"""

async def query_agent_node(state: AgentState, config) -> dict:
    """
    Executes the Query Agent node in LangGraph.
    Passes current message logs to ChatGroq, executes tool requests, and appends responses.
    """
    messages = state["messages"]
    agent_messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)

    response = await query_agent_llm.ainvoke(agent_messages, config)
    new_messages = [response]

    if response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]
            
            if tool_name in READ_TOOLS:
                tool_func = READ_TOOLS[tool_name]
                print(f"[Query Agent] Executing read tool: {tool_name} with arguments: {tool_args}")
                
                tool_output = await tool_func.ainvoke(tool_args, config)

                tool_msg = ToolMessage(
                    content=str(tool_output),
                    tool_call_id=tool_id,
                    name=tool_name
                )
                new_messages.append(tool_msg)
                
                state_update = {"messages": new_messages}

                if "project_id" in tool_args:
                    state_update["current_project_id"] = str(tool_args["project_id"])
                
                final_response = await model.ainvoke(agent_messages + new_messages, config)
                new_messages.append(final_response)
                
                return {
                    "messages": new_messages,
                    **({"current_project_id": str(tool_args["project_id"])} if "project_id" in tool_args else {})
                }
            
    return {"messages": new_messages}
