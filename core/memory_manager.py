"""
Memory & Context System (Phase 6).

A local SQLite database that lets Nova remember facts the user tells it
("Nova, remember my project name is Quantum") and recall recent
conversation turns for context. Matches the user_memory /
conversation_history schema from the NOVA design doc.
"""

import datetime
import os
import sqlite3


class MemoryManager:
    def __init__(self, db_path: str = "data/nova_system.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.initialize_memory_database()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def initialize_memory_database(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_memory (
                    memory_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    memory_key TEXT UNIQUE,
                    memory_value TEXT,
                    timestamp DATETIME,
                    source TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversation_history (
                    conversation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_input TEXT,
                    nova_response TEXT,
                    timestamp DATETIME
                )
            """)
            conn.commit()

    # ---------- facts ----------

    def store_memory(self, key: str, value: str, source: str = "user") -> None:
        """Stores or overwrites a fact, e.g. key='project_name', value='Quantum'."""
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO user_memory (memory_key, memory_value, timestamp, source)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(memory_key) DO UPDATE SET
                    memory_value = excluded.memory_value,
                    timestamp = excluded.timestamp,
                    source = excluded.source
            """, (key, value, datetime.datetime.now().isoformat(), source))
            conn.commit()

    def retrieve_memory(self, key: str):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT memory_value FROM user_memory WHERE memory_key = ?", (key,)
            ).fetchone()
        return row[0] if row else None

    def update_memory(self, key: str, value: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                "UPDATE user_memory SET memory_value = ?, timestamp = ? WHERE memory_key = ?",
                (value, datetime.datetime.now().isoformat(), key),
            )
            conn.commit()
            return cur.rowcount > 0

    def delete_memory(self, key: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM user_memory WHERE memory_key = ?", (key,))
            conn.commit()
            return cur.rowcount > 0

    def list_all_memories(self) -> list:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT memory_key, memory_value FROM user_memory ORDER BY timestamp DESC"
            ).fetchall()
        return [{"key": k, "value": v} for k, v in rows]

    # ---------- conversation history ----------

    def store_conversation_history(self, user_input: str, nova_response: str) -> None:
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO conversation_history (user_input, nova_response, timestamp)
                VALUES (?, ?, ?)
            """, (user_input, nova_response, datetime.datetime.now().isoformat()))
            conn.commit()

    def retrieve_conversation_context(self, limit: int = 5) -> list:
        """Returns the most recent `limit` conversation turns, oldest first."""
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT user_input, nova_response, timestamp
                FROM conversation_history
                ORDER BY conversation_id DESC
                LIMIT ?
            """, (limit,)).fetchall()
        rows.reverse()
        return [
            {"user_input": u, "nova_response": r, "timestamp": t}
            for u, r, t in rows
        ]
