"""
Memory module — conversation history manage karta hai.
SQLite se persist karta hai + in-memory cache.
"""
import datetime
import time

# In-memory cache
_memory_store: dict = {}


def create_session(user_id: int = 1) -> int:
    from backend.database import db_execute, DB_AVAILABLE
    if DB_AVAILABLE:
        sid = db_execute(
            "INSERT INTO sessions (user_id, created_at) VALUES (?, ?)",
            (user_id, datetime.datetime.now().isoformat())
        )
        if sid:
            return sid
    return int(time.time())


def save_message(session_id: int, user_id: int, role: str, content: str, is_relevant: bool = True):
    # In-memory
    if session_id not in _memory_store:
        _memory_store[session_id] = []
    _memory_store[session_id].append({"role": role, "content": content})
    if len(_memory_store[session_id]) > 30:
        _memory_store[session_id] = _memory_store[session_id][-30:]

    # SQLite
    from backend.database import db_execute, DB_AVAILABLE
    if DB_AVAILABLE:
        db_execute(
            "INSERT INTO messages (session_id, user_id, role, content, is_relevant, timestamp) VALUES (?,?,?,?,?,?)",
            (session_id, user_id, role, content, int(is_relevant), datetime.datetime.now().isoformat())
        )


def get_history(session_id: int) -> list:
    """Return last 10 messages."""
    if session_id in _memory_store:
        return _memory_store[session_id][-10:]

    from backend.database import db_execute, DB_AVAILABLE
    if DB_AVAILABLE:
        rows = db_execute(
            "SELECT role, content FROM messages WHERE session_id=? ORDER BY id ASC LIMIT 10",
            (session_id,),
            fetch='all'
        )
        if rows:
            return [{"role": r["role"], "content": r["content"]} for r in rows]
    return []
