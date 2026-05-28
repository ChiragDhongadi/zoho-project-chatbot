from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, ToolMessage, AIMessage
from backend.app.config import settings
from backend.app.agents.state import AgentState
from backend.app.agents.tools import create_task, update_task, delete_task

model = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model=settings.GROQ_MODEL,
    temperature=0.0
)

WRITE_TOOLS = {
    "create_task": create_task,
    "update_task": update_task,
    "delete_task": delete_task
}

action_agent_llm = model.bind_tools(list(WRITE_TOOLS.values()))

SYSTEM_PROMPT = """You are the specialized Action Agent for Zoho Projects.
Your sole responsibility is to handle WRITE requests (creating, updating, assigning, or deleting tasks).

RULES:
1. You are strictly a WRITE agent. You MUST NOT attempt to fetch or list general projects or members unless it is directly required to complete a write operation.
2. Short-term Memory Context: Pay close attention to previous messages. If a user asks to "delete task #5" and there is a task #5 listed under project 'P1' earlier, assume the project_id is 'P1'.
3. Always ask the user for details if fields are missing, but once you have them, call the appropriate tool.
"""

async def action_agent_node(state: AgentState, config) -> dict:
    """
    Executes the Action Agent node.
    Intercepts write tool calls, saves them as a pending action, and halts for user confirmation.
    If already confirmed, it executes the tool.
    """
    messages = state.get("messages", [])
    action_confirmed = state.get("action_confirmed")
    pending_action = state.get("pending_action")


    # FLOW A: USER HAS CONFIRMED THE PENDING ACTION

    if action_confirmed is True and pending_action:
        tool_name = pending_action["tool"]
        tool_args = pending_action["args"]
        
        tool_func = WRITE_TOOLS.get(tool_name)
        if not tool_func:
            return {"messages": [AIMessage(content="Error: Pending action tool not found.")], "pending_action": None, "action_confirmed": None}

        print(f"[Action Agent] User CONFIRMED. Executing write tool: {tool_name} with arguments: {tool_args}")

        tool_output = await tool_func.ainvoke(tool_args, config)

        dummy_ai = AIMessage(
            content="", 
            tool_calls=[{"name": tool_name, "args": tool_args, "id": "hil_call_id"}]
        )

        tool_msg = ToolMessage(
            content=str(tool_output),
            tool_call_id="hil_call_id",
            name=tool_name
        )

        agent_messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages) + [dummy_ai, tool_msg]
        
        final_summary = await model.ainvoke(agent_messages, config)

        return {
            "messages": [tool_msg, final_summary],
            "pending_action": None,
            "action_confirmed": None
        }


    # FLOW B: USER HAS DECLINED THE PENDING ACTION

    if action_confirmed is False and pending_action:
        print("[Action Agent] User DECLINED the pending action. Aborting.")
        abort_msg = AIMessage(content="Operation canceled cleanly. No changes were made to your Zoho account.")
        return {
            "messages": [abort_msg],
            "pending_action": None,
            "action_confirmed": None
        }

    
    # FLOW C: LLM ANALYZING USER QUERY & SELECTING TOOL

    agent_messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)
    response = await action_agent_llm.ainvoke(agent_messages, config)


    if response.tool_calls:
        tool_call = response.tool_calls[0]
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]


        if tool_name in WRITE_TOOLS:
            print(f"[Action Agent] Intercepted tool: {tool_name}. Halting for Human-in-the-Loop validation.")

            description = f"Action: {tool_name.replace('_', ' ').title()}\n"
            description += "\n".join([f"  * {k}: {v}" for k, v in tool_args.items()])

            pending_payload = {
                "tool": tool_name,
                "args": tool_args,
                "description": description
            }

            prompt_msg = AIMessage(
                content=f"**Human-in-the-Loop Confirmation Required** \n\nI am ready to perform the following action:\n```\n{description}\n```\nWould you like to confirm and execute this operation?"
            )

            return {
                "messages": [prompt_msg],
                "pending_action": pending_payload,
                "action_confirmed": None
            }

    return {"messages": [response]}
