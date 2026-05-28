import aiosqlite
from fastapi import Request, HTTPException, Depends, Security
from fastapi.security import APIKeyHeader
from backend.app.db.database import get_db

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

async def get_current_user(
    request: Request,
    db: aiosqlite.Connection = Depends(get_db),
    auth_header: str = Security(api_key_header)
) -> str:
    """
    Dependency that extracts and validates the active session_id from 
    Headers, Cookies, or Query Parameters.
    """
    session_id = None

    if auth_header:
        if auth_header.startswith("Bearer "):
            session_id = auth_header.replace("Bearer ", "")
        else:
            session_id = auth_header

    if not session_id:
        session_id = request.cookies.get("session_id")

    if not session_id:
        session_id = request.query_params.get("session_id")

    if not session_id:
        raise HTTPException(
            status_code=401, 
            detail="Session missing or unauthenticated. Please log in."
        )

    async with db.execute(
        "SELECT user_id, email FROM user_tokens WHERE user_id = ?", 
        (session_id,)
    ) as cursor:
        row = await cursor.fetchone()
        
    if not row:
        raise HTTPException(
            status_code=401, 
            detail="Invalid session ID or session has expired. Please log in again."
        )

    return row["user_id"]
