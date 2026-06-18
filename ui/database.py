import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "onboarding.db"
)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email      TEXT PRIMARY KEY,
            name       TEXT NOT NULL,
            password   TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id         TEXT PRIMARY KEY,
            user_email TEXT NOT NULL,
            title      TEXT NOT NULL,
            messages   TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_email) REFERENCES users(email)
        )
    """)
    conn.commit()
    conn.close()
    print("✅ Database initialised at", DB_PATH)


def create_user(email: str, name: str, hashed_password: str) -> bool:
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO users (email, name, password, created_at) VALUES (?, ?, ?, ?)",
            (email, name, hashed_password, datetime.utcnow().isoformat()),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def get_user(email: str) -> dict | None:
    conn = get_connection()
    row  = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_chats(user_email: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, user_email, title, messages, created_at, updated_at FROM chats WHERE user_email = ? ORDER BY updated_at DESC",
        (user_email,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def upsert_chat(user_email: str, chat_id: str, title: str, messages: str) -> None:
    now  = datetime.utcnow().isoformat()
    conn = get_connection()
    existing = conn.execute("SELECT id FROM chats WHERE id = ?", (chat_id,)).fetchone()

    if existing:
        conn.execute(
            "UPDATE chats SET title = ?, messages = ?, updated_at = ? WHERE id = ?",
            (title, messages, now, chat_id),
        )
    else:
        conn.execute(
            "INSERT INTO chats (id, user_email, title, messages, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (chat_id, user_email, title, messages, now, now),
        )
    conn.commit()
    conn.close()


def delete_chat(chat_id: str) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
    conn.commit()
    conn.close()