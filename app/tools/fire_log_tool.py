"""Fire / smoke alarm log analysis tool.

Reads data/logs/fire_alarm_log.csv and produces summary statistics.
"""

import csv
from collections import Counter
from pathlib import Path


def query_fire_log(
    log_path: str = "data/logs/fire_alarm_log.csv",
    recent_n: int = 10,
) -> dict:
    """Read fire_alarm_log.csv and build a summary dict.

    Args:
        log_path: Path to the CSV log file.
        recent_n: How many recent alarms to return.

    Returns:
        dict with:
            - total_alarms
            - by_level: {HIGH: N, MEDIUM: N}
            - by_event: {fire: N, smoke: N, ...}
            - recent: list of last recent_n records (newest first)
            - log_exists: bool
            - error: str if file not found
    """
    log_path = Path(log_path)

    if not log_path.exists():
        return {
            "log_exists": False,
            "error": f"Fire alarm log not found: {log_path}. "
                     f"Run fire detection first.",
            "total_alarms": 0,
            "by_level": {},
            "by_event": {},
            "recent": [],
        }

    records: list[dict] = []
    with open(log_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)

    total = len(records)

    # ── Count by alarm level ───────────────────────────────────────
    level_counter = Counter(r["alarm_level"] for r in records)
    by_level = dict(level_counter.most_common())

    # ── Count by event type ────────────────────────────────────────
    event_counter = Counter(r["event_type"] for r in records)
    by_event = dict(event_counter.most_common())

    # ── Most recent N ──────────────────────────────────────────────
    recent = records[-recent_n:] if records else []
    recent.reverse()

    return {
        "log_exists": True,
        "total_alarms": total,
        "by_level": by_level,
        "by_event": by_event,
        "recent": recent,
        "recent_count": len(recent),
    }


def build_markdown_summary(result: dict) -> str:
    """Turn a query_fire_log result into a Markdown string."""
    if not result.get("log_exists"):
        return f"*{result.get('error', 'No log available.')}*"

    lines = [
        f"**Total alarms**: {result['total_alarms']}",
        "",
        "**By level**:",
    ]
    for level, count in result.get("by_level", {}).items():
        emoji = "🔴" if level == "HIGH" else "🟡"
        lines.append(f"  - {emoji} `{level}`: {count}")

    lines.append("")
    lines.append("**By event type**:")
    for event, count in result.get("by_event", {}).items():
        lines.append(f"  - `{event}`: {count}")

    recent = result.get("recent", [])
    if recent:
        lines.append("")
        lines.append(f"**Recent {len(recent)} alarms**:")
        for r in recent:
            lines.append(
                f"  - `{r.get('alarm_level')}` "
                f"{r.get('class_name')} "
                f"{r.get('confidence')} "
                f"— {r.get('reason', '')}"
            )

    return "\n".join(lines)
