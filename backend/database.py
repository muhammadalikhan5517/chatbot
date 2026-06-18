"""
Database module — Pure SQLite3 (no SQLAlchemy needed).
Lightweight, zero-dependency, deployment-ready.
"""
import sqlite3
import datetime
import os
from backend.config import DB_PATH

DB_AVAILABLE = False
_conn = None


def _get_conn():
    """Thread-safe SQLite connection."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables if they don't exist."""
    global DB_AVAILABLE
    try:
        conn = _get_conn()
        c = conn.cursor()

        c.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                city TEXT,
                education_level TEXT,
                language_preference TEXT DEFAULT 'auto',
                interested_course TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                user_id INTEGER,
                role TEXT,
                content TEXT,
                is_relevant INTEGER DEFAULT 1,
                feedback TEXT,
                timestamp TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS unanswered_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT,
                timestamp TEXT DEFAULT (datetime('now'))
            );
        """)

        conn.commit()
        conn.close()
        DB_AVAILABLE = True
        print(f"[DB] SQLite initialized: {DB_PATH}")
    except Exception as e:
        print(f"[DB] Init failed: {e}")
        DB_AVAILABLE = False


def db_execute(query: str, params: tuple = (), fetch: str = None):
    """
    Execute a query safely.
    fetch: None | 'one' | 'all'
    Returns lastrowid for INSERT, rows for SELECT, None on error.
    """
    try:
        conn = _get_conn()
        c = conn.cursor()
        c.execute(query, params)
        if fetch == 'one':
            result = c.fetchone()
            conn.close()
            return result
        elif fetch == 'all':
            result = c.fetchall()
            conn.close()
            return result
        else:
            conn.commit()
            last_id = c.lastrowid
            conn.close()
            return last_id
    except Exception as e:
        print(f"[DB] Query error: {e} | Query: {query[:60]}")
        return None
