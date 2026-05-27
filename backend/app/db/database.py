import os
import sqlite3
import aiosqlite
from backend.app.config import settings

DB_PATH = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")

async def init_db():
    """Initializes the SQLite database and creates the required tables."""
    db_dir = os.path.dirname(DB_PATH)

    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    
    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_tokens (
                user_id TEXT PRIMARY KEY,
                email TEXT,
                access_token TEXT NOT NULL,
                refresh_token TEXT NOT NULL,
                expires_at REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS long_term_memory (
                user_id TEXT,
                key TEXT,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, key)
            )
        """)

        await db.commit()

    print("Database initialized successfully and tables verified.")


async def get_db():
    """Dependency to retrieve an active, async SQLite database connection."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db