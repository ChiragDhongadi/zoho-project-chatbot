from typing import TypedDict, Annotated, Sequence, Optional, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):

    messages: Annotated[Sequence[BaseMessage], add_messages]
    user_id: str  
    current_project_id: Optional[str]
    current_project_name: Optional[str]
    pending_action: Optional[Dict[str, Any]]
    action_confirmed: Optional[bool]
    long_term_memory: Optional[str]