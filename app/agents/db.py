"""SQLite repository for disposal steps and work orders."""

from __future__ import annotations

import logging
import sqlite3
import threading
from pathlib import Path
from typing import Any

from app.config import DB_PATH

logger = logging.getLogger(__name__)

_db_path = str(Path(DB_PATH))
_local = threading.local()
_schema_lock = threading.Lock()


def configure_db(path: str | Path) -> None:
    """Switch the repository path, primarily for isolated tests."""
    global _db_path
    close_connection()
    _db_path = str(Path(path))


def close_connection() -> None:
    connection = getattr(_local, "conn", None)
    if connection is not None:
        connection.close()
        _local.conn = None


def _get_conn() -> sqlite3.Connection:
    """Return a thread-local connection with bounded lock waiting."""
    if getattr(_local, "conn", None) is None:
        Path(_db_path).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(_db_path, timeout=5.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout=5000")
        with _schema_lock:
            connection.execute("PRAGMA journal_mode=WAL")
            _init_db(connection)
        _local.conn = connection
    return _local.conn


def _init_db(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS disposal_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL,
            step_name TEXT NOT NULL DEFAULT '',
            content TEXT NOT NULL DEFAULT '',
            event_type TEXT NOT NULL DEFAULT '',
            alarm_level TEXT NOT NULL DEFAULT '',
            location TEXT NOT NULL DEFAULT '',
            event_timestamp TEXT NOT NULL DEFAULT '',
            work_order_id TEXT NOT NULL DEFAULT '',
            final_report TEXT NOT NULL DEFAULT '',
            notification_sent INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );
        CREATE TABLE IF NOT EXISTS work_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT NOT NULL UNIQUE,
            event_id TEXT NOT NULL,
            event_type TEXT NOT NULL DEFAULT '',
            alarm_level TEXT NOT NULL DEFAULT '',
            location TEXT NOT NULL DEFAULT '',
            actions TEXT NOT NULL DEFAULT '',
            analysis TEXT NOT NULL DEFAULT '',
            regulations TEXT NOT NULL DEFAULT '',
            assigned_to TEXT NOT NULL DEFAULT 'On-site Safety Team',
            final_report TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );
        """
    )
    _ensure_columns(
        connection,
        "work_orders",
        {
            "analysis": "TEXT NOT NULL DEFAULT ''",
            "regulations": "TEXT NOT NULL DEFAULT ''",
            "final_report": "TEXT NOT NULL DEFAULT ''",
            "updated_at": "TEXT NOT NULL DEFAULT ''",
        },
    )
    _ensure_columns(
        connection,
        "disposal_log",
        {
            "step_name": "TEXT NOT NULL DEFAULT ''",
            "content": "TEXT NOT NULL DEFAULT ''",
            "event_timestamp": "TEXT NOT NULL DEFAULT ''",
        },
    )
    connection.commit()


def _ensure_columns(
    connection: sqlite3.Connection,
    table: str,
    columns: dict[str, str],
) -> None:
    existing = {row["name"] for row in connection.execute(f"PRAGMA table_info({table})")}
    for name, declaration in columns.items():
        if name not in existing:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {name} {declaration}")


def _write(sql: str, values: tuple[Any, ...]) -> int:
    connection = _get_conn()
    try:
        cursor = connection.execute(sql, values)
        connection.commit()
        return int(cursor.lastrowid or 0)
    except sqlite3.Error:
        connection.rollback()
        raise


def insert_disposal_step(event_id: str, step_name: str, content: str, timestamp: str) -> int:
    """Persist one observable workflow step."""
    return _write(
        """INSERT INTO disposal_log
           (event_id, step_name, content, event_timestamp)
           VALUES (?, ?, ?, ?)""",
        (str(event_id), str(step_name)[:100], str(content)[:1000], str(timestamp)),
    )


def insert_disposal_log(
    *,
    event_id: str,
    event_type: str,
    alarm_level: str,
    location: str,
    timestamp: str,
    work_order_id: str = "",
    final_report: str = "",
    notification_sent: bool = False,
) -> int:
    """Persist the final disposal record with an explicit schema."""
    return _write(
        """INSERT INTO disposal_log
           (event_id, event_type, alarm_level, location, event_timestamp,
            work_order_id, final_report, notification_sent)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            event_id,
            event_type,
            alarm_level,
            location,
            timestamp,
            work_order_id,
            final_report,
            int(notification_sent),
        ),
    )


def insert_work_order(
    *,
    order_id: str,
    event_id: str,
    event_type: str,
    alarm_level: str,
    location: str,
    actions: str = "",
    dispatch: str = "",
    analysis: str = "",
    regulations: str = "",
    assigned_to: str = "On-site Safety Team",
    final_report: str = "",
    status: str = "pending",
) -> int:
    """Create one work order; duplicate order IDs keep the original record."""
    return _write(
        """INSERT OR IGNORE INTO work_orders
           (order_id, event_id, event_type, alarm_level, location, actions,
            analysis, regulations, assigned_to, final_report, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            order_id,
            event_id,
            event_type,
            alarm_level,
            location,
            actions or dispatch,
            analysis,
            regulations,
            assigned_to,
            final_report,
            status,
        ),
    )


def update_work_order(order_id: str, final_report: str, status: str = "completed") -> bool:
    connection = _get_conn()
    try:
        cursor = connection.execute(
            """UPDATE work_orders
               SET final_report = ?, status = ?, updated_at = datetime('now', 'localtime')
               WHERE order_id = ?""",
            (final_report, status, order_id),
        )
        connection.commit()
        return cursor.rowcount == 1
    except sqlite3.Error:
        connection.rollback()
        raise


def get_work_order(order_id: str) -> dict[str, Any] | None:
    row = _get_conn().execute(
        "SELECT * FROM work_orders WHERE order_id = ?",
        (order_id,),
    ).fetchone()
    return dict(row) if row is not None else None


def list_disposal_steps(event_id: str) -> list[dict[str, Any]]:
    rows = _get_conn().execute(
        """SELECT event_id, step_name, content, event_timestamp
           FROM disposal_log WHERE event_id = ? AND step_name != '' ORDER BY id""",
        (event_id,),
    ).fetchall()
    return [dict(row) for row in rows]
