"""
SQLite storage utility for optional persistent conversation history in VisionQA.
Provides simple, thread-safe persistence using Python's built-in sqlite3.
"""

import sqlite3
import datetime
from typing import List, Dict, Any, Optional

DB_PATH = "visionqa_history.db"


def get_db_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Create a database connection with row factory enabled."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DB_PATH) -> None:
    """Initialize SQLite database tables if they do not exist."""
    conn = get_db_connection(db_path)
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                title TEXT,
                image_metadata TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT,
                role TEXT,
                content TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations (conversation_id) ON DELETE CASCADE
            )
        """)
    conn.close()


def save_conversation_meta(conversation_id: str, title: str = "VisionQA Chat", metadata_str: str = "", db_path: str = DB_PATH) -> None:
    """Record or update conversation entry."""
    conn = get_db_connection(db_path)
    with conn:
        conn.execute("""
            INSERT OR IGNORE INTO conversations (conversation_id, title, image_metadata)
            VALUES (?, ?, ?)
        """, (conversation_id, title, metadata_str))
    conn.close()


def save_message_to_db(conversation_id: str, role: str, content: str, db_path: str = DB_PATH) -> None:
    """Append a message to the conversation history in SQLite."""
    conn = get_db_connection(db_path)
    with conn:
        conn.execute("""
            INSERT INTO messages (conversation_id, role, content)
            VALUES (?, ?, ?)
        """, (conversation_id, role, content))
    conn.close()


def load_conversation_messages(conversation_id: str, db_path: str = DB_PATH) -> List[Dict[str, str]]:
    """Retrieve all messages for a specific conversation ID."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT role, content FROM messages
        WHERE conversation_id = ?
        ORDER BY id ASC
    """, (conversation_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"role": row["role"], "content": row["content"]} for row in rows]


def get_saved_conversations(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Get list of past conversations with message counts."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.conversation_id, c.created_at, c.title, COUNT(m.id) as message_count
        FROM conversations c
        LEFT JOIN messages m ON c.conversation_id = m.conversation_id
        GROUP BY c.conversation_id
        ORDER BY c.created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "conversation_id": row["conversation_id"],
            "created_at": row["created_at"],
            "title": row["title"],
            "message_count": row["message_count"]
        }
        for row in rows
    ]


def clear_history_db(db_path: str = DB_PATH) -> None:
    """Clear all records from database."""
    conn = get_db_connection(db_path)
    with conn:
        conn.execute("DELETE FROM messages")
        conn.execute("DELETE FROM conversations")
    conn.close()
