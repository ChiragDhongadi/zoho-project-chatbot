import uuid
import time
import httpx
from fastapi import APIRouter, Request, Query, HTTPException, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from backend.app.config import settings
from backend.app.db.database import get_db
import aiosqlite

router = APIRouter(prefix="/auth", tags=["Authentication"])

ZOHO_AUTH_URL = f"https://accounts.{settings.ZOHO_DOMAIN}/oauth/v2/auth"
ZOHO_TOKEN_URL = f"https://accounts.{settings.ZOHO_DOMAIN}/oauth/v2/token"

SCOPES = [
    "ZohoProjects.portals.READ",
    "ZohoProjects.projects.READ",
    "ZohoProjects.tasks.CREATE",
    "ZohoProjects.tasks.READ",
    "ZohoProjects.tasks.UPDATE",
    "ZohoProjects.tasks.DELETE",
    "ZohoProjects.users.READ"
]

@router.get("/login")
def login():
    """Redirects the user to Zoho's OAuth consent screen."""
    scope_str = ",".join(SCOPES)
    params = {
        "client_id": settings.ZOHO_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": settings.ZOHO_REDIRECT_URI,
        "scope": scope_str,
        "access_type": "offline",  # Crucial to get a refresh token
        "prompt": "consent"      # Forces Zoho to present consent page to return refresh_token
    }
    
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    auth_redirect_url = f"{ZOHO_AUTH_URL}?{query_string}"
    
    return RedirectResponse(url=auth_redirect_url)

@router.get("/callback")
async def callback(
    code: str = Query(None), 
    error: str = Query(None),
    db: aiosqlite.Connection = Depends(get_db)
):
    """Handles Zoho's redirect callback and exchanges the auth code for tokens."""
    if error:
        raise HTTPException(status_code=400, detail=f"Zoho OAuth error: {error}")
    
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code is missing.")

    payload = {
        "code": code,
        "client_id": settings.ZOHO_CLIENT_ID,
        "client_secret": settings.ZOHO_CLIENT_SECRET,
        "redirect_uri": settings.ZOHO_REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(ZOHO_TOKEN_URL, data=payload)
        token_data = response.json()

    if "error" in token_data:
        raise HTTPException(
            status_code=400, 
            detail=f"Token exchange failed: {token_data.get('error_description', token_data['error'])}"
        )

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", 3600)  
    
    if not refresh_token:
        print("Warning: Refresh token not sent by Zoho in this callback.")

    expires_at = time.time() + expires_in

    session_id = f"session_{uuid.uuid4().hex}"
    
    email_placeholder = "authenticated_zoho_user"

    await db.execute(
        """
        INSERT OR REPLACE INTO user_tokens (user_id, email, access_token, refresh_token, expires_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (session_id, email_placeholder, access_token, refresh_token or "", expires_at)
    )
    await db.commit()

    frontend_url = f"http://localhost:5173?session_id={session_id}"
    
    response = RedirectResponse(url=frontend_url)
    
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        max_age=30 * 24 * 3600, # 30 days
        samesite="lax"
    )
    
    return response

@router.get("/session")
async def check_session(
    session_id: str = Query(None), 
    db: aiosqlite.Connection = Depends(get_db)
):
    """Endpoint for the React frontend to verify if a session is valid."""
    if not session_id:
        return JSONResponse(status_code=401, content={"authenticated": False, "detail": "No session ID provided"})

    async with db.execute(
        "SELECT user_id, email, expires_at FROM user_tokens WHERE user_id = ?", 
        (session_id,)
    ) as cursor:
        row = await cursor.fetchone()
        
    if not row:
        return JSONResponse(status_code=401, content={"authenticated": False, "detail": "Invalid session ID"})

    return {
        "authenticated": True,
        "session_id": row["user_id"],
        "email": row["email"]
    }
