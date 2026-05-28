import json
from typing import Optional
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langchain_core.pydantic_v1 import BaseModel, Field
from backend.app.zoho.client import ZohoClient


# Pydantic Input Schemas for all 8 Tools (Hiding config parameter)

class ListProjectsInput(BaseModel):
    pass

class ListTasksInput(BaseModel):
    project_id: str = Field(..., description="Zoho Project ID (Required)")
    status: Optional[str] = Field(None, description="Filter by status: e.g. 'open' or 'closed'")
    assignee_id: Optional[str] = Field(None, description="Zoho Owner/User ID to filter tasks by assignee")
    due_date: Optional[str] = Field(None, description="Filter by due date format (MM-DD-YYYY)")

class GetTaskDetailsInput(BaseModel):
    project_id: str = Field(..., description="Zoho Project ID (Required)")
    task_id: str = Field(..., description="Zoho Task ID (Required)")

class ListProjectMembersInput(BaseModel):
    pass

class GetTaskUtilisationInput(BaseModel):
    project_id: str = Field(..., description="Zoho Project ID (Required)")

class CreateTaskInput(BaseModel):
    project_id: str = Field(..., description="Zoho Project ID (Required)")
    name: str = Field(..., description="Task title/name (Required)")
    description: Optional[str] = Field(None, description="Task description")
    owner_id: Optional[str] = Field(None, description="Zoho User ID to assign this task to")
    due_date: Optional[str] = Field(None, description="Format: MM-DD-YYYY")
    priority: Optional[str] = Field(None, description="Task priority: 'None', 'Low', 'Medium', 'High'")

class UpdateTaskInput(BaseModel):
    project_id: str = Field(..., description="Zoho Project ID (Required)")
    task_id: str = Field(..., description="Zoho Task ID to modify (Required)")
    name: Optional[str] = Field(None, description="New name for the task")
    description: Optional[str] = Field(None, description="New description")
    owner_id: Optional[str] = Field(None, description="New assignee Zoho User ID")
    due_date: Optional[str] = Field(None, description="Format: MM-DD-YYYY")
    priority: Optional[str] = Field(None, description="Task priority: 'None', 'Low', 'Medium', 'High'")

class DeleteTaskInput(BaseModel):
    project_id: str = Field(..., description="Zoho Project ID (Required)")
    task_id: str = Field(..., description="Zoho Task ID to delete (Required)")


# READ-ONLY TOOLS (Query Agent Tools)

@tool(args_schema=ListProjectsInput)
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

@tool(args_schema=ListTasksInput)
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

@tool(args_schema=GetTaskDetailsInput)
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

@tool(args_schema=ListProjectMembersInput)
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

@tool(args_schema=GetTaskUtilisationInput)
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


# WRITE TOOLS (Action Agent Tools - Intercepted by HIL)

@tool(args_schema=CreateTaskInput)
async def create_task(
    project_id: str,
    name: str,
    description: Optional[str] = None,
    owner_id: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: Optional[str] = None,
    config: RunnableConfig = None
) -> str:
    """
    Create a new task under a specific Zoho project.
    Use this when creating tasks on approval.
    """
    session_id = config["configurable"].get("session_id")
    db = config["configurable"].get("db")
    
    client = ZohoClient(session_id, db)

    task_payload = {"name": name}
    if description:
        task_payload["description"] = description
    if owner_id:
        task_payload["person_responsible"] = owner_id
    if due_date:
        task_payload["due_date"] = due_date
    if priority:
        task_payload["priority"] = priority

    try:
        task = await client.create_task(project_id, task_payload)
        return f"SUCCESS: Task '{task.get('name')}' created successfully. Task ID: {task.get('id')}."
    except Exception as e:
        return f"ERROR: Failed to create task: {str(e)}"

@tool(args_schema=UpdateTaskInput)
async def update_task(
    project_id: str,
    task_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    owner_id: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: Optional[str] = None,
    config: RunnableConfig = None
) -> str:
    """
    Update details of an existing task under a specific project.
    Use this when updating or assigning a task.
    """
    session_id = config["configurable"].get("session_id")
    db = config["configurable"].get("db")
    
    client = ZohoClient(session_id, db)
    
    task_payload = {}
    if name:
        task_payload["name"] = name
    if description:
        task_payload["description"] = description
    if owner_id:
        task_payload["person_responsible"] = owner_id
    if due_date:
        task_payload["due_date"] = due_date
    if priority:
        task_payload["priority"] = priority

    try:
        task = await client.update_task(project_id, task_id, task_payload)
        return f"SUCCESS: Task '{task_id}' updated successfully."
    except Exception as e:
        return f"ERROR: Failed to update task: {str(e)}"

@tool(args_schema=DeleteTaskInput)
async def delete_task(
    project_id: str,
    task_id: str,
    config: RunnableConfig = None
) -> str:
    """
    Delete a task under a specific project by its ID.
    Use this when deleting a task on approval.
    """
    session_id = config["configurable"].get("session_id")
    db = config["configurable"].get("db")
    
    client = ZohoClient(session_id, db)
    try:
        await client.delete_task(project_id, task_id)
        return f"SUCCESS: Task '{task_id}' has been permanently deleted."
        
    except Exception as e:
        return f"ERROR: Failed to delete task: {str(e)}"
