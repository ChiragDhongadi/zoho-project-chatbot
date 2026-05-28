import uvicorn
from typing import Optional, Dict, Any
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import aiosqlite
from backend.app.config import settings
from backend.app.db.database import get_db, init_db
from backend.app.auth.router import router as auth_router
from backend.app.auth.middleware import get_current_user
from backend.app.agents.graph import compiled_graph
from backend.app.agents.memory import get_long_term_memory_prompt, save_long_term_memory

app = FastAPI(
    title="Zoho Projects AI Chatbot API",
    description="Multi-agent stateful LangGraph backend exposing natural language Zoho Projects integration.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    await init_db()

app.include_router(auth_router)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    pending_action: Optional[Dict[str, Any]] = None

class ConfirmRequest(BaseModel):
    confirmed: bool


@app.get("/")
def read_root():
    return {"status": "healthy", "message": "Zoho Projects Chatbot API is online and validated!"}

@app.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    session_id: str = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    """
    Main chat handler endpoint.
    Retrieves user session context, loads memories, invokes LangGraph, 
    and handles state-driven responses.
    """
    user_message = payload.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Empty query.")

    lt_memory_prompt = await get_long_term_memory_prompt(session_id, db)

    config = {
        "configurable": {
            "thread_id": session_id,
            "session_id": session_id,
            "db": db
        }
    }

    input_state = {
        "messages": [("user", user_message)],
        "user_id": session_id,
        "long_term_memory": lt_memory_prompt
    }

    try:
        state_output = await compiled_graph.ainvoke(input_state, config)
        
        messages = state_output.get("messages", [])
        ai_reply = "No response generated."
        
        for msg in reversed(messages):
            if msg.type == "ai" and msg.content:
                ai_reply = msg.content
                break

        active_proj_id = state_output.get("current_project_id")
        if active_proj_id:
            proj_payload = {"id": active_proj_id, "name": f"Project #{active_proj_id}"}
            await save_long_term_memory(session_id, "last_accessed_project", proj_payload, db)

        pending_action = state_output.get("pending_action")

        return ChatResponse(
            reply=ai_reply,
            pending_action=pending_action
        )

    except Exception as e:
        print(f"[Error in Chat Endpoint]: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Graph Execution Error: {str(e)}")

@app.post("/chat/confirm", response_model=ChatResponse)
async def chat_confirm(
    payload: ConfirmRequest,
    session_id: str = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    """
    Confirms or declines a pending intercepted HIL write action.
    Resumes graph execution.
    """
    config = {
        "configurable": {
            "thread_id": session_id,
            "session_id": session_id,
            "db": db
        }
    }

    current_state = await compiled_graph.aget_state(config)
    state_values = current_state.values

    pending_action = state_values.get("pending_action")
    if not pending_action:
        raise HTTPException(
            status_code=400, 
            detail="No pending operation found awaiting confirmation for this session."
        )

    update_payload = {
        "action_confirmed": payload.confirmed
    }
    
    await compiled_graph.aupdate_state(config, update_payload)

    try:
        resumed_state = await compiled_graph.ainvoke(None, config)
        
        messages = resumed_state.get("messages", [])
        ai_reply = "Operation completed."
        for msg in reversed(messages):
            if msg.type == "ai" and msg.content:
                ai_reply = msg.content
                break

        return ChatResponse(
            reply=ai_reply,
            pending_action=None 
        )

    except Exception as e:
        print(f"[Error in Confirm Endpoint]: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Graph Execution Resume Error: {str(e)}")
