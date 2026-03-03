"""SQLite persistence for webhook events."""

import json
import os
import sqlite3

from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("WEBHOOK_DB", "webhooks.db")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the events table if it does not exist."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def add_event(data: dict, timestamp: str) -> int:
    """Insert a webhook event and return its row ID."""
    with _connect() as conn:
        cursor = conn.execute(
            "INSERT INTO events (data, timestamp) VALUES (?, ?)",
            (json.dumps(data), timestamp),
        )
        return cursor.lastrowid


def get_events(limit: int = 200) -> list[dict]:
    """Return the most recent events, newest first."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT data, timestamp FROM events ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [{"data": json.loads(row["data"]), "timestamp": row["timestamp"]} for row in rows]


def clear_events() -> None:
    """Delete all stored events."""
    with _connect() as conn:
        conn.execute("DELETE FROM events")
