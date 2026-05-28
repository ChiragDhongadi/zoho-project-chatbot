import json
import time
import aiosqlite
from typing import Dict, Any, Optional

async def save_long_term_memory(
    user_id: str, 
    key: str, 
    value: Any, 
    db: aiosqlite.Connection
):
    """
    Persists a piece of long-term memory (JSON serializable) for a specific user.
    """
    serialized_value = json.dumps(value)
    await db.execute(
        """
        INSERT OR REPLACE INTO long_term_memory (user_id, key, value, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (user_id, key, serialized_value)
    )
    await db.commit()
    print(f"[Long-Term Memory] Saved memory '{key}' for user '{user_id}'.")

async def load_long_term_memory(
    user_id: str, 
    db: aiosqlite.Connection
) -> Dict[str, Any]:
    """
    Loads all long-term memory key-values for a given user.
    """
    memories = {}
    async with db.execute(
        "SELECT key, value FROM long_term_memory WHERE user_id = ?",
        (user_id,)
    ) as cursor:
        rows = await cursor.fetchall()
        for row in rows:
            try:
                memories[row["key"]] = json.loads(row["value"])
            except Exception:
                memories[row["key"]] = row["value"]
    return memories

async def get_long_term_memory_prompt(
    user_id: str, 
    db: aiosqlite.Connection
) -> str:
    """
    Loads long-term memory for a user and formats it into a prompt snippet
    that can be appended to the Agent System Prompts.
    """
    memories = await load_long_term_memory(user_id, db)
    if not memories:
        return ""
        
    prompt_lines = [
        "\n[LONG-TERM MEMORY (PAST SESSIONS CONTEXT)]",
        "You have retrieved the following context about this user from previous sessions:"
    ]
    
    if "last_accessed_project" in memories:
        proj = memories["last_accessed_project"]
        prompt_lines.append(f"- Last active project the user worked on: {proj.get('name')} (ID: {proj.get('id')})")
        
    if "user_preferences" in memories:
        prefs = memories["user_preferences"]
        for k, v in prefs.items():
            prompt_lines.append(f"- User Preference - {k}: {v}")
            
    prompt_lines.append("Use this context to personalize your greetings and suggest relevant default actions.")
    return "\n".join(prompt_lines)
