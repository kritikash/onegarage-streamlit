"""SQLite persistence layer for chat history."""

import sqlite3
from datetime import datetime

import streamlit as st


DB_PATH = "chat_history.db"


@st.cache_resource
def get_connection() -> sqlite3.Connection:
    """Return a singleton SQLite connection with WAL mode."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    _init_schema(conn)
    return conn


def _init_schema(conn: sqlite3.Connection) -> None:
    """Create tables if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS chats (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL DEFAULT 'New Chat',
            favorite INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()


def _run_migrations() -> None:
    """Ensure schema is up-to-date (runs on every import, cheap check)."""
    conn = get_connection()
    try:
        conn.execute("SELECT favorite FROM chats LIMIT 0")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE chats ADD COLUMN favorite INTEGER NOT NULL DEFAULT 0")
        conn.commit()


_run_migrations()


# ── Chat CRUD ───────────────────────────────────────────────


def create_chat(chat_id: str, title: str = "New Chat") -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO chats (id, title) VALUES (?, ?)",
        (chat_id, title),
    )
    conn.commit()


def list_chats() -> list[dict]:
    """Return all chats ordered by most recently updated."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, title, favorite, created_at, updated_at FROM chats ORDER BY updated_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def get_chat(chat_id: str) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM chats WHERE id = ?", (chat_id,)).fetchone()
    return dict(row) if row else None


def update_chat_title(chat_id: str, title: str) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE chats SET title = ?, updated_at = ? WHERE id = ?",
        (title, datetime.now().isoformat(), chat_id),
    )
    conn.commit()


def touch_chat(chat_id: str) -> None:
    """Update the updated_at timestamp."""
    conn = get_connection()
    conn.execute(
        "UPDATE chats SET updated_at = ? WHERE id = ?",
        (datetime.now().isoformat(), chat_id),
    )
    conn.commit()


def delete_chat(chat_id: str) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
    conn.commit()


# ── Favorites ────────────────────────────────────────────────


def toggle_favorite(chat_id: str) -> bool:
    """Toggle the favorite flag on a chat. Returns the new state."""
    conn = get_connection()
    row = conn.execute("SELECT favorite FROM chats WHERE id = ?", (chat_id,)).fetchone()
    if not row:
        return False
    new_val = 0 if row["favorite"] else 1
    conn.execute("UPDATE chats SET favorite = ? WHERE id = ?", (new_val, chat_id))
    conn.commit()
    return bool(new_val)


def is_favorite(chat_id: str) -> bool:
    conn = get_connection()
    row = conn.execute("SELECT favorite FROM chats WHERE id = ?", (chat_id,)).fetchone()
    return bool(row["favorite"]) if row else False


def list_favorites() -> list[dict]:
    """Return all favorited chats ordered by most recently updated."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, title, created_at, updated_at FROM chats WHERE favorite = 1 ORDER BY updated_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


# ── Message CRUD ────────────────────────────────────────────


def add_message(chat_id: str, role: str, content: str) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
        (chat_id, role, content),
    )
    conn.commit()
    touch_chat(chat_id)


def list_messages(chat_id: str) -> list[dict]:
    """Return all messages for a chat in chronological order."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT role, content, created_at FROM messages WHERE chat_id = ? ORDER BY id ASC",
        (chat_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_message_preview(chat_id: str, max_length: int = 80) -> str:
    """Return a short preview of the first user message in a chat."""
    conn = get_connection()
    row = conn.execute(
        "SELECT content FROM messages WHERE chat_id = ? AND role = 'user' ORDER BY id ASC LIMIT 1",
        (chat_id,),
    ).fetchone()
    if not row:
        return ""
    text = row["content"]
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(" ", 1)[0] + "..."


def delete_last_exchange(chat_id: str) -> str | None:
    """Delete the last user + assistant message pair. Returns the user message content."""
    conn = get_connection()
    # Get last user message
    row = conn.execute(
        "SELECT id, content FROM messages WHERE chat_id = ? AND role = 'user' ORDER BY id DESC LIMIT 1",
        (chat_id,),
    ).fetchone()
    if not row:
        return None
    user_content = row["content"]
    user_id = row["id"]

    # Delete assistant messages after this user message
    conn.execute(
        "DELETE FROM messages WHERE chat_id = ? AND role = 'assistant' AND id > ?",
        (chat_id, user_id),
    )
    # Delete the user message itself
    conn.execute("DELETE FROM messages WHERE id = ?", (user_id,))
    conn.commit()
    return user_content
