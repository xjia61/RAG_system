import sqlite3
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "chat_history.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_chat_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            title TEXT,
            created_at TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            created_at TEXT,
            FOREIGN KEY(session_id) REFERENCES sessions(session_id)
        )
        """
    )

    conn.commit()
    conn.close()


def create_chat_session(title: str = "New Chat") -> Dict:
    init_chat_db()

    session_id = uuid.uuid4().hex
    created_at = datetime.now().isoformat(timespec="seconds")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO sessions (session_id, title, created_at)
        VALUES (?, ?, ?)
        """,
        (session_id, title, created_at),
    )

    conn.commit()
    conn.close()

    return {
        "session_id": session_id,
        "title": title,
        "created_at": created_at,
    }


def add_chat_message(
    session_id: str,
    role: str,
    content: str,
) -> Dict:
    init_chat_db()

    if role not in ["user", "assistant", "system"]:
        return {"error": "role must be user, assistant, or system"}

    created_at = datetime.now().isoformat(timespec="seconds")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO messages (session_id, role, content, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (session_id, role, content, created_at),
    )

    conn.commit()
    conn.close()

    return {
        "session_id": session_id,
        "role": role,
        "content": content,
        "created_at": created_at,
    }


def get_chat_history(
    session_id: str,
    limit: int = 20,
) -> List[Dict]:
    init_chat_db()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT role, content, created_at
        FROM messages
        WHERE session_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (session_id, limit),
    )

    rows = cur.fetchall()
    conn.close()

    # reverse back to chronological order
    rows = list(reversed(rows))

    return [
        {
            "role": row["role"],
            "content": row["content"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def format_chat_history_for_prompt(
    session_id: Optional[str],
    limit: int = 10,
) -> str:
    if not session_id:
        return ""

    messages = get_chat_history(session_id=session_id, limit=limit)

    if not messages:
        return ""

    lines = []

    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        lines.append(f"{role}: {content}")

    return "\n".join(lines)


def list_chat_sessions(limit: int = 20) -> List[Dict]:
    init_chat_db()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT session_id, title, created_at
        FROM sessions
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "session_id": row["session_id"],
            "title": row["title"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def clear_chat_session(session_id: str) -> Dict:
    init_chat_db()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM messages
        WHERE session_id = ?
        """,
        (session_id,),
    )

    conn.commit()
    conn.close()

    return {
        "message": "Chat session cleared",
        "session_id": session_id,
    }