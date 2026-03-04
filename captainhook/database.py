"""Database persistence for webhook events.

Supports SurrealDB (via HTTP API) when SURREALDB_URL is set,
otherwise falls back to SQLite for local development.
"""

import json
import logging
import os
import sqlite3
import time

import requests as req
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── SurrealDB config ────────────────────────────────────────────────────────

SURREALDB_URL = os.getenv("SURREALDB_URL", "").rstrip("/")
SURREALDB_NS = os.getenv("SURREALDB_NS", "captainhook")
SURREALDB_DB = os.getenv("SURREALDB_DB", "captainhook")
SURREALDB_USER = os.getenv("SURREALDB_USER", "root")
SURREALDB_PASS = os.getenv("SURREALDB_PASS", "root")

# ── SQLite config (fallback) ────────────────────────────────────────────────

DB_PATH = os.getenv("WEBHOOK_DB", "webhooks.db")


def _use_surrealdb() -> bool:
    return bool(SURREALDB_URL)


# ── SurrealDB helpers ───────────────────────────────────────────────────────


def _surreal_query(sql: str, retries: int = 3) -> list:
    """Execute a SurrealQL query via HTTP API with retry logic."""
    headers = {
        "Accept": "application/json",
        "surreal-ns": SURREALDB_NS,
        "surreal-db": SURREALDB_DB,
    }
    for attempt in range(retries):
        try:
            resp = req.post(
                f"{SURREALDB_URL}/sql",
                data=sql,
                headers=headers,
                auth=(SURREALDB_USER, SURREALDB_PASS),
                timeout=10,
            )
            resp.raise_for_status()
            results = resp.json()
            # SurrealDB returns a list of statement results
            for r in results:
                if r.get("status") == "ERR":
                    raise RuntimeError(f"SurrealDB error: {r.get('result')}")
            return results
        except req.RequestException as exc:
            if attempt < retries - 1:
                wait = 2 ** attempt
                logger.warning(
                    "SurrealDB connection failed (attempt %d/%d), retrying in %ds: %s",
                    attempt + 1, retries, wait, exc,
                )
                time.sleep(wait)
            else:
                raise
    return []


# ── SQLite helpers ──────────────────────────────────────────────────────────


def _sqlite_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── Public interface ────────────────────────────────────────────────────────


def init_db() -> None:
    """Create the events table/schema if it does not exist."""
    if _use_surrealdb():
        _surreal_query("""
            DEFINE TABLE IF NOT EXISTS events SCHEMAFULL;
            DEFINE FIELD IF NOT EXISTS payload ON events FLEXIBLE TYPE object;
            DEFINE FIELD IF NOT EXISTS timestamp ON events TYPE string;
            DEFINE FIELD IF NOT EXISTS created_at ON events TYPE datetime DEFAULT time::now();
        """)
        logger.info("SurrealDB schema initialized (%s)", SURREALDB_URL)
    else:
        with _sqlite_connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
        logger.info("SQLite database initialized (%s)", DB_PATH)


def add_event(data: dict, timestamp: str) -> str | int:
    """Insert a webhook event. Returns the record ID."""
    if _use_surrealdb():
        results = _surreal_query(
            f"CREATE events SET payload = {json.dumps(data)}, timestamp = '{timestamp}';"
        )
        record = results[0].get("result", [{}])
        if isinstance(record, list) and record:
            return record[0].get("id", "")
        return ""
    else:
        with _sqlite_connect() as conn:
            cursor = conn.execute(
                "INSERT INTO events (data, timestamp) VALUES (?, ?)",
                (json.dumps(data), timestamp),
            )
            return cursor.lastrowid


def get_events(limit: int = 200) -> list[dict]:
    """Return the most recent events, newest first."""
    if _use_surrealdb():
        results = _surreal_query(
            f"SELECT * FROM events ORDER BY created_at DESC LIMIT {limit};"
        )
        rows = results[0].get("result", []) if results else []
        return [
            {"data": row.get("payload", {}), "timestamp": row.get("timestamp", "")}
            for row in rows
        ]
    else:
        with _sqlite_connect() as conn:
            rows = conn.execute(
                "SELECT data, timestamp FROM events ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {"data": json.loads(row["data"]), "timestamp": row["timestamp"]}
            for row in rows
        ]


def clear_events() -> None:
    """Delete all stored events."""
    if _use_surrealdb():
        _surreal_query("DELETE FROM events;")
    else:
        with _sqlite_connect() as conn:
            conn.execute("DELETE FROM events")
