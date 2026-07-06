"""SQLite database for work orders and disposal logs.

Tables:
  - work_order:   structured disposal work orders
  - disposal_log: step-by-step execution log

Uses standard library sqlite3, no ORM.
"""

from __future__ import annotations

import sqlite3
import threading
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DB_PATH = str(Path(__file__).resolve().parent.parent / "data" / "work_order.db")

# Thread-local connections for safety
_local = threading.local()


def _get_conn() -> sqlite3.Connection:
    """Get or create a thread-local SQLite connection."""
    if not hasattr(_local, "conn") or _local.conn is None:
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA foreign_keys=ON")
    return _local.conn


# ---------------------------------------------------------------------------
# Schema initialization
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create tables if they don't exist. Idempotent, safe to call on startup."""
    conn = _get_conn()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS work_order (
            order_id     TEXT PRIMARY KEY,
            event_id     TEXT NOT NULL,
            event_type   TEXT NOT NULL,
            alarm_level  TEXT NOT NULL,
            location     TEXT DEFAULT '',
            analysis     TEXT DEFAULT '',
            regulations  TEXT DEFAULT '',
            dispatch     TEXT DEFAULT '',
            final_report TEXT DEFAULT '',
            create_time  TEXT NOT NULL,
            status       TEXT DEFAULT 'pending'
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS disposal_log (
            log_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id     TEXT NOT NULL,
            step_name    TEXT NOT NULL,
            step_content TEXT DEFAULT '',
            timestamp    TEXT NOT NULL
        )
    """)

    conn.commit()


# ---------------------------------------------------------------------------
# CRUD operations
# ---------------------------------------------------------------------------

def insert_work_order(
    order_id: str,
    event_id: str,
    event_type: str,
    alarm_level: str,
    location: str = "",
    analysis: str = "",
    regulations: str = "",
    dispatch: str = "",
    final_report: str = "",
    status: str = "pending",
) -> None:
    """Insert a new work order."""
    conn = _get_conn()
    create_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        """INSERT OR REPLACE INTO work_order
           (order_id, event_id, event_type, alarm_level, location,
            analysis, regulations, dispatch, final_report, create_time, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (order_id, event_id, event_type, alarm_level, location,
         analysis, regulations, dispatch, final_report, create_time, status),
    )
    conn.commit()


def insert_disposal_log(
    event_id: str,
    step_name: str,
    step_content: str = "",
    timestamp: str | None = None,
) -> None:
    """Insert a disposal step log entry."""
    conn = _get_conn()
    ts = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        """INSERT INTO disposal_log (event_id, step_name, step_content, timestamp)
           VALUES (?, ?, ?, ?)""",
        (event_id, step_name, step_content, ts),
    )
    conn.commit()


def query_orders_by_level(alarm_level: str, limit: int = 20) -> list[dict]:
    """Query work orders filtered by alarm level."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM work_order WHERE alarm_level = ? ORDER BY create_time DESC LIMIT ?",
        (alarm_level, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def query_orders_by_event(event_id: str) -> list[dict]:
    """Query work orders for a specific event."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM work_order WHERE event_id = ? ORDER BY create_time DESC",
        (event_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def query_recent_orders(limit: int = 20) -> list[dict]:
    """Query most recent work orders."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM work_order ORDER BY create_time DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def query_disposal_logs(event_id: str) -> list[dict]:
    """Query disposal step logs for an event."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM disposal_log WHERE event_id = ? ORDER BY log_id ASC",
        (event_id,),
    ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Auto-initialize on import
# ---------------------------------------------------------------------------

init_db()
