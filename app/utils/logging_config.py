# -*- coding: utf-8 -*-
"""Structured logging configuration for RoboVision-Agent.

Provides a single ``setup_logging()`` call that configures:
  - Console output (human-readable)
  - File output (JSON, one record per line, for log aggregation)

Usage::

    from app.utils.logging_config import setup_logging
    setup_logging()

    import logging
    logger = logging.getLogger(__name__)
    logger.info("detection complete", extra={"objects": 5})
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from app.config import LOG_DIR


class JSONFormatter(logging.Formatter):
    """Emit one JSON object per log line for machine parsing."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # Attach any extra fields
        for key, value in record.__dict__.items():
            if key not in (
                "args", "asctime", "created", "exc_info", "exc_text",
                "filename", "funcName", "levelname", "levelno", "lineno",
                "message", "module", "msecs", "msg", "name", "pathname",
                "process", "processName", "relativeCreated", "stack_info",
                "thread", "threadName",
            ):
                log_entry[key] = value
        if record.exc_info and not record.exc_text:
            log_entry["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False, default=str)


def setup_logging(
    level: str | int = logging.INFO,
    log_file: str | Path | None = None,
) -> None:
    """Configure root logger with console + file handlers.

    Args:
        level:     Logging level (name or int).
        log_file:  Override path for the JSON log file.
                   Defaults to ``data/logs/robovision.log``.
    """
    root = logging.getLogger()
    root.setLevel(level)

    # Prevent duplicate handlers on repeated calls
    if root.handlers:
        return

    # Console: human-readable
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)-5s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    root.addHandler(console)

    # File: JSON (for log aggregation / debugging)
    log_path = Path(log_file) if log_file else LOG_DIR / "robovision.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(str(log_path), encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONFormatter())
    root.addHandler(file_handler)
