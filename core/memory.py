import sqlite3
import json
from typing import List, Dict
from config.settings import settings

class ConversationMemory:
    def __init__(self):
        self.db_path = settings.STORAGE_DIR / "sqlite" / "chat_history.db"
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tool_calls TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def add_message(self, role: str, content: str, tool_calls: list = None):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO messages (role, content, tool_calls) VALUES (?, ?, ?)",
                (role, content, json.dumps(tool_calls) if tool_calls else None)
            )

    def get_recent_history(self, limit: int = 10) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT role, content FROM messages ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

memory = ConversationMemory()