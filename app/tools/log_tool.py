"""Log analysis tool — reads and queries detection logs."""

import csv
from collections import Counter
from pathlib import Path


def query_log(
    log_path: str = "data/logs/detection_log.csv",
    recent_n: int = 10,
    low_conf_threshold: float = 0.3,
) -> dict:
    """Read detection_log.csv and build a query result dict.

    Args:
        log_path: Path to the CSV log file.
        recent_n: How many of the most recent records to return.
        low_conf_threshold: Confidence below this is considered "low".

    Returns:
        dict with:
            - total:               total record count
            - class_distribution:  {class_name: count, ...} sorted desc
            - num_classes:         unique class count
            - recent:              last recent_n records (newest first)
            - low_confidence:      all records below threshold
            - low_confidence_count
            - log_exists:          bool
            - error:               str if file not found
    """
    log_path = Path(log_path)

    if not log_path.exists():
        return {
            "log_exists": False,
            "error": f"Log file not found: {log_path}. "
                     f"Run video detection first.",
            "total": 0,
            "class_distribution": {},
            "num_classes": 0,
            "recent": [],
            "low_confidence": [],
            "low_confidence_count": 0,
            "threshold": low_conf_threshold,
        }

    records: list[dict] = []
    with open(log_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)

    total = len(records)

    # ── Class distribution ─────────────────────────────────────────
    class_counter = Counter(r["class_name"] for r in records)
    class_distribution = dict(class_counter.most_common())

    # ── Most recent N (latest at end of file, so slice then reverse) ─
    recent = records[-recent_n:] if records else []
    recent.reverse()  # newest first

    # ── Low-confidence samples ─────────────────────────────────────
    low_conf = [
        r for r in records
        if float(r["confidence"]) < low_conf_threshold
    ]

    return {
        "log_exists": True,
        "total": total,
        "class_distribution": class_distribution,
        "num_classes": len(class_distribution),
        "recent": recent,
        "recent_count": len(recent),
        "low_confidence": low_conf,
        "low_confidence_count": len(low_conf),
        "threshold": low_conf_threshold,
    }
