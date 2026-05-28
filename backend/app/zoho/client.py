import time
import httpx
import aiosqlite
from typing import Dict, Any, List, Optional
from backend.app.config import settings

class ZohoClient:
    """
    An OOP client representing a user's session with Zoho Projects.
    Handles token retrieval, silent automatic token refresh, dynamic portal detection,
    and maps the API endpoints needed for the 8 core agent tools.
    """
    
    def __init__(self, session_id: str, db: aiosqlite.Connection):
        self.session_id = session_id
        self.db = db
        self.base_url = f"https://projectsapi.{settings.ZOHO_DOMAIN}/v3"
        self.token_url = f"https://accounts.{settings.ZOHO_DOMAIN}/oauth/v2/token"
        self._portal_id: Optional[str] = None

    async def _get_tokens(self) -> Dict[str, Any]:
        """Helper to fetch current credentials from the database."""
        async with self.db.execute(
            "SELECT access_token, refresh_token, expires_at FROM user_tokens WHERE user_id = ?",
            (self.session_id,)
        ) as cursor:
            row = await cursor.fetchone()
            
        if not row:
            raise ValueError(f"No authentication record found for session: {self.session_id}")
            
        return {
            "access_token": row["access_token"],
            "refresh_token": row["refresh_token"],
            "expires_at": row["expires_at"]
        }

    async def get_valid_token(self) -> str:
        """
        Retrieves the access token, automatically refreshing it
        if it has expired or is expiring in less than 60 seconds.
        """
        tokens = await self._get_tokens()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        expires_at = tokens["expires_at"]

        # Checking if expired or expiring in under 60 seconds
        if time.time() >= (expires_at - 60):
            print(f"[ZohoClient] Token expiring soon. Initiating automatic silent refresh for session {self.session_id}...")
            
            if not refresh_token:
                raise ValueError("Cannot refresh Zoho access token: refresh token is missing.")

            payload = {
                "refresh_token": refresh_token,
                "client_id": settings.ZOHO_CLIENT_ID,
                "client_secret": settings.ZOHO_CLIENT_SECRET,
                "grant_type": "refresh_token"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(self.token_url, data=payload)
                refresh_data = response.json()

            if "error" in refresh_data:
                raise ValueError(f"Failed to refresh access token: {refresh_data.get('error')}")

            access_token = refresh_data["access_token"]
            expires_in = refresh_data.get("expires_in", 3600)
            new_expires_at = time.time() + expires_in

            await self.db.execute(
                """
                UPDATE user_tokens 
                SET access_token = ?, expires_at = ? 
                WHERE user_id = ?
                """,
                (access_token, new_expires_at, self.session_id)
            )
            await self.db.commit()
            print("[ZohoClient] Token refreshed successfully.")

        return access_token

    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None, 
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Wrapper to make authenticated HTTP requests with automated token loading."""
        token = await self.get_valid_token()
        headers = {
            "Authorization": f"Zoho-oauthtoken {token}",
            "Accept": "application/json"
        }

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        async with httpx.AsyncClient() as client:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = await client.post(url, headers=headers, json=json_data)
            elif method.upper() == "PUT":
                response = await client.put(url, headers=headers, json=json_data)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()
            
            if response.status_code == 204 or not response.content:
                return {}
                
            return response.json()

    async def get_portal_id(self) -> str:
        """
        Dynamically fetches the first active portal ID from Zoho Projects.
        Stores it in memory for the duration of the request to prevent redundant API calls.
        """

        if settings.ZOHO_PORTAL_ID:
            return settings.ZOHO_PORTAL_ID
            
        if self._portal_id:
            return self._portal_id

        portals_data = await self._request("GET", "/portals/")
        portals = portals_data.get("portals", [])
        
        if not portals:
            raise ValueError("No Zoho Projects portals found for this authenticated user.")
            
        self._portal_id = str(portals[0]["id"])
        return self._portal_id


    # Tool wrappers (for the 8 required integrations)

    async def list_projects(self) -> List[Dict[str, Any]]:
        """Lists all projects for the authenticated user."""
        portal_id = await self.get_portal_id()
        data = await self._request("GET", f"/portal/{portal_id}/projects/")
        return data.get("projects", [])

    async def list_tasks(
        self, 
        project_id: str, 
        status: Optional[str] = None, 
        assignee_id: Optional[str] = None,
        due_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List tasks for a project with optional filters."""
        portal_id = await self.get_portal_id()
        params = {}
        if status:
            params["status"] = status
        if assignee_id:
            params["owner"] = assignee_id
        if due_date:
            params["due_date"] = due_date
            
        data = await self._request("GET", f"/portal/{portal_id}/projects/{project_id}/tasks/", params=params)
        return data.get("tasks", [])

    async def get_task_details(self, project_id: str, task_id: str) -> Dict[str, Any]:
        """Fetch details of a single task by ID."""
        portal_id = await self.get_portal_id()
        data = await self._request("GET", f"/portal/{portal_id}/projects/{project_id}/tasks/{task_id}/")
        tasks = data.get("tasks", [])
        return tasks[0] if tasks else {}


    async def create_task(self, project_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task in a given project."""
        portal_id = await self.get_portal_id()
        data = await self._request("POST", f"/portal/{portal_id}/projects/{project_id}/tasks/", json_data=task_data)
        tasks = data.get("tasks", [])
        return tasks[0] if tasks else {}

    async def update_task(self, project_id: str, task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a task (status, assignee, due date, or priority)."""
        portal_id = await self.get_portal_id()
        data = await self._request("PUT", f"/portal/{portal_id}/projects/{project_id}/tasks/{task_id}/", json_data=task_data)
        tasks = data.get("tasks", [])
        return tasks[0] if tasks else {}

    async def delete_task(self, project_id: str, task_id: str) -> bool:
        """Delete a task (requires Human-In-The-Loop confirmation in agent logic)."""
        portal_id = await self.get_portal_id()
        await self._request("DELETE", f"/portal/{portal_id}/projects/{project_id}/tasks/{task_id}/")
        return True

    async def list_project_members(self) -> List[Dict[str, Any]]:
        """Get all members of the active portal/projects."""
        portal_id = await self.get_portal_id()
        data = await self._request("GET", f"/portal/{portal_id}/users/")
        return data.get("users", [])

    async def get_task_utilisation(self, project_id: str) -> Dict[str, Any]:
        """
        Summarizes the task load per member across a project.
        Fetches all active tasks and computes member aggregation statistics.
        """
        portal_id = await self.get_portal_id()
        tasks = await self.list_tasks(project_id)
        members = await self.list_project_members()
        member_map = {str(m["id"]): m["name"] for m in members}
        utilisation = {}
        unassigned_count = 0
        
        for task in tasks:
            owners = task.get("owners", [])
            
            if not owners:
                unassigned_count += 1
                continue
                
            for owner in owners:
                owner_id = str(owner.get("id"))
                owner_name = owner.get("name") or member_map.get(owner_id, f"User {owner_id}")
                
                if owner_name not in utilisation:
                    utilisation[owner_name] = {
                        "total_tasks": 0,
                        "open_tasks": 0,
                        "closed_tasks": 0
                    }
                
                utilisation[owner_name]["total_tasks"] += 1
                
                status_name = task.get("status", {}).get("name", "").lower()
                if "closed" in status_name or "completed" in status_name:
                    utilisation[owner_name]["closed_tasks"] += 1
                else:
                    utilisation[owner_name]["open_tasks"] += 1
                    
        return {
            "project_id": project_id,
            "member_utilisation": utilisation,
            "unassigned_tasks": unassigned_count,
            "total_tasks_fetched": len(tasks)
        }
