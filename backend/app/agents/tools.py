import json
from typing import Optional
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from backend.app.zoho.client import ZohoClient


# READ-ONLY TOOLS (Query Agent Tools)

@tool
async def list_projects(config: RunnableConfig) -> str:
    """
    Fetch all active Zoho projects for the authenticated user.
    Use this when the user asks to list their projects or when you need to find a project ID.
    """
    session_id = config["configurable"].get("session_id")
    db = config["configurable"].get("db")
    
    client = ZohoClient(session_id, db)
    
    try:
        projects = await client.list_projects()

        if not projects:
            return "No projects found."
        
        formatted = []
        for p in projects:
            formatted.append(f"- Project Name: {p['name']} | ID: {p['id']} | Status: {p['status']}")
        return "\n".join(formatted)

    except Exception as e:
        return f"Error fetching projects: {str(e)}"

@tool
async def list_tasks(
    project_id: str,
    status: Optional[str] = None,
    assignee_id: Optional[str] = None,
    due_date: Optional[str] = None,
    config: RunnableConfig = None
) -> str:
    """
    List tasks under a specific Zoho project with optional filters.
    Use this when listing tasks or looking up tasks.
    Filters:
      - status: e.g. 'open', 'closed'
      - assignee_id: Zoho Owner User ID to filter tasks by assignee
      - due_date: Filter by due date format (MM-DD-YYYY)
    """
    session_id = config["configurable"].get("session_id")
    db = config["configurable"].get("db")
    
    client = ZohoClient(session_id, db)

    try:
        tasks = await client.list_tasks(project_id, status, assignee_id, due_date)

        if not tasks:
            return f"No tasks found for project ID {project_id} matching the filters."
            
        formatted = []
        for t in tasks:
            assignee = t.get("owner_name") or "Unassigned"
            formatted.append(
                f"- Task Name: {t['name']} | ID: {t['id']} | Status: {t.get('status', {}).get('name', 'N/A')} | Assignee: {assignee} | Due Date: {t.get('due_date', 'None')}"
            )

        return "\n".join(formatted)

    except Exception as e:
        return f"Error listing tasks: {str(e)}"

@tool
async def get_task_details(
    project_id: str,
    task_id: str,
    config: RunnableConfig
) -> str:
    """
    Fetch comprehensive details of a single task by its ID under a specific project.
    Use this when the user asks for in-depth information about a specific task.
    """
    session_id = config["configurable"].get("session_id")
    db = config["configurable"].get("db")
    
    client = ZohoClient(session_id, db)

    try:
        task = await client.get_task_details(project_id, task_id)

        if not task:
            return f"Task with ID {task_id} not found in project {project_id}."
            
        return json.dumps(task, indent=2)

    except Exception as e:
        return f"Error fetching task details: {str(e)}"

@tool
async def list_project_members(config: RunnableConfig) -> str:
    """
    Retrieve all users and members of the Zoho Projects portal along with their roles and IDs.
    Use this when you need to find an assignee's ID or list members.
    """
    session_id = config["configurable"].get("session_id")
    db = config["configurable"].get("db")
    
    client = ZohoClient(session_id, db)

    try:
        members = await client.list_project_members()

        if not members:
            return "No portal members found."
            
        formatted = []
        for m in members:
            formatted.append(f"- Name: {m['name']} | ID: {m['id']} | Email: {m['email']} | Role: {m.get('role', 'Member')}")
        return "\n".join(formatted)

    except Exception as e:
        return f"Error fetching project members: {str(e)}"

@tool
async def get_task_utilisation(
    project_id: str,
    config: RunnableConfig
) -> str:
    """
    Summarize task load per member across a project. Evaluates how many tasks are open
    or completed per user. Use this to answer queries like 'Who has the most tasks?'
    or 'Summarize task load'.
    """
    session_id = config["configurable"].get("session_id")
    db = config["configurable"].get("db")
    
    client = ZohoClient(session_id, db)

    try:
        res = await client.get_task_utilisation(project_id)

        formatted = [
            f"Task Utilization Summary for Project {project_id}:",
            f"- Total Tasks Fetched: {res['total_tasks_fetched']}",
            f"- Unassigned Tasks: {res['unassigned_tasks']}",
            "\nBreakdown by Member:"
        ]
        
        for member, stats in res["member_utilisation"].items():
            formatted.append(
                f"  * {member}: {stats['open_tasks']} Open, {stats['closed_tasks']} Closed (Total: {stats['total_tasks']})"
            )
            
        return "\n".join(formatted)

    except Exception as e:
        return f"Error fetching task utilization: {str(e)}"
