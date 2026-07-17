# -*- coding: utf-8 -*-
"""Unified event logger for RoboVision Agent.

Writes all detection and alarm events to a single CSV log.
"""

import csv
import threading
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# configuration
# ---------------------------------------------------------------------------

DEFAULT_LOG_PATH = Path("data/logs/event_log.csv")

# CSV columns in order
COLUMNS = [
    "timestamp",
    "task_type",
    "media_type",
    "source",
    "frame_id",
    "class_name",
    "confidence",
    "bbox",
    "is_alarm",
    "alarm_level",
    "event_type",
    "output_image",
    "alarm_image",
    "reason",
]

# thread safety for concurrent writes
_lock = threading.Lock()


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------

def append_event(event: dict, log_path: str | None = None):
    """Append one event row to the unified event log.

    If the log file does not exist it is created with a header row.
    Missing keys are filled with an empty string.

    Args:
        event:    dict with keys matching COLUMNS (partial OK).
        log_path: override path; defaults to data/logs/event_log.csv.
    """
    path = Path(log_path) if log_path else DEFAULT_LOG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    # fill missing fields with empty string
    row = {}
    for col in COLUMNS:
        val = event.get(col, "")
        # bbox may be a list -> convert to string
        if isinstance(val, list):
            val = str(val)
        row[col] = val

    # timestamp auto-fill if not provided
    if not row["timestamp"]:
        row["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")

    with _lock:
        write_header = not path.exists() or path.stat().st_size == 0
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS)
            if write_header:
                writer.writeheader()
            writer.writerow(row)
