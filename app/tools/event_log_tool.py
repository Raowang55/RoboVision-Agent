# -*- coding: utf-8 -*-
"""Unified event log analysis tool.

Reads data/logs/event_log.csv and provides query / summary capabilities.
"""

import csv
import time
from collections import Counter
from pathlib import Path

from app.config import LOW_CONF_THRESHOLD, REPORTS_DIR


def query_event_log(
    log_path: str = "data/logs/event_log.csv",
    recent_n: int = 10,
    low_conf_threshold: float = LOW_CONF_THRESHOLD,
) -> dict:
    """Read the unified event log and build a query result dict.

    Args:
        log_path:           Path to the CSV log file.
        recent_n:           How many recent alarms to return.
        low_conf_threshold: Confidence below this is considered "low".

    Returns:
        dict with:
            - log_exists:          bool
            - error:               str if file not found
            - total_events:        int
            - total_alarms:        int  (is_alarm == "True")
            - by_task_type:        {task_type: count}
            - by_class_name:       {class_name: count}
            - by_alarm_level:      {HIGH: N, MEDIUM: N, ...}
            - recent_alarms:       list[dict]  -- newest first
            - recent_alarm_count:  int
            - low_confidence:      list[dict]
            - low_confidence_count:int
            - threshold:           float
    """
    log_path = Path(log_path)

    if not log_path.exists():
        return {
            "log_exists": False,
            "error": (
                f"Event log not found: {log_path}. "
                "Run detection or alarm monitoring first."
            ),
            "total_events": 0,
            "total_alarms": 0,
            "by_task_type": {},
            "by_class_name": {},
            "by_alarm_level": {},
            "recent_alarms": [],
            "recent_alarm_count": 0,
            "low_confidence": [],
            "low_confidence_count": 0,
            "threshold": low_conf_threshold,
        }

    records: list[dict] = []
    with open(log_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)

    total_events = len(records)

    # ---- totals ----
    alarms = [r for r in records if r.get("is_alarm", "").lower() == "true"]
    total_alarms = len(alarms)

    # ---- by task_type ----
    task_counter = Counter(r.get("task_type", "?") for r in records)
    by_task_type = dict(task_counter.most_common())

    # ---- by class_name ----
    class_counter = Counter(r.get("class_name", "?") for r in records)
    by_class_name = dict(class_counter.most_common())

    # ---- by alarm_level ----
    level_counter = Counter(
        r.get("alarm_level", "") for r in records if r.get("alarm_level")
    )
    by_alarm_level = dict(level_counter.most_common())

    # ---- recent alarms (newest first) ----
    recent_alarms = alarms[-recent_n:] if alarms else []
    recent_alarms.reverse()

    # ---- low confidence ----
    low_conf = [
        r for r in records
        if float(r.get("confidence", 1.0)) < low_conf_threshold
    ]

    return {
        "log_exists": True,
        "total_events": total_events,
        "total_alarms": total_alarms,
        "by_task_type": by_task_type,
        "by_class_name": by_class_name,
        "by_alarm_level": by_alarm_level,
        "recent_alarms": recent_alarms,
        "recent_alarm_count": len(recent_alarms),
        "low_confidence": low_conf,
        "low_confidence_count": len(low_conf),
        "threshold": low_conf_threshold,
    }


def query_event_log_filtered(
    log_path: str = "data/logs/event_log.csv",
    alarm_level: str = "ALL",
    event_type: str = "ALL",
    start_date: str = "",
    end_date: str = "",
    recent_n: int = 20,
) -> dict:
    """Read the unified event log with structured filtering.

    Args:
        log_path:      Path to the CSV log file.
        alarm_level:   Filter by alarm level (ALL, HIGH, MEDIUM, LOW).
        event_type:    Filter by class_name (ALL, fire, smoke, no_helmet, no_vest).
        start_date:    Start date filter (YYYY-MM-DD), empty = no lower bound.
        end_date:      End date filter (YYYY-MM-DD), empty = no upper bound.
        recent_n:      Max number of filtered records to return.

    Returns:
        dict with:
            - log_exists:        bool
            - total:             int  (total records in file)
            - filtered_count:    int  (records after applying filters)
            - records:           list[dict]  -- filtered records, newest first
            - alarm_images:      list[str]  -- alarm image paths that exist
            - stats:             dict  -- {HIGH: N, MEDIUM: N, LOW: N} counts
    """
    from datetime import datetime as dt_datetime

    log_path = Path(log_path)

    if not log_path.exists():
        return {
            "log_exists": False,
            "total": 0,
            "filtered_count": 0,
            "records": [],
            "alarm_images": [],
            "stats": {},
            "error": f"Event log not found: {log_path}",
        }

    records: list[dict] = []
    with open(log_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)

    total = len(records)

    # Filter by alarm_level
    if alarm_level != "ALL":
        records = [
            r for r in records
            if r.get("alarm_level", "").upper() == alarm_level.upper()
        ]

    # Filter by event_type (match against class_name column)
    if event_type != "ALL":
        records = [
            r for r in records
            if r.get("class_name", "").lower() == event_type.lower()
        ]

    # Filter by date range (match against timestamp column)
    if start_date:
        try:
            start_dt = dt_datetime.strptime(start_date, "%Y-%m-%d")
            records = [
                r for r in records
                if dt_datetime.strptime(r.get("timestamp", "1970-01-01")[:10], "%Y-%m-%d") >= start_dt
            ]
        except ValueError:
            pass  # invalid date format, skip filter

    if end_date:
        try:
            end_dt = dt_datetime.strptime(end_date, "%Y-%m-%d")
            records = [
                r for r in records
                if dt_datetime.strptime(r.get("timestamp", "1970-01-01")[:10], "%Y-%m-%d") <= end_dt
            ]
        except ValueError:
            pass  # invalid date format, skip filter

    filtered_count = len(records)

    # Take most recent N records (reversed so newest first)
    display_records = records[-recent_n:] if records else []
    display_records.reverse()

    # Collect alarm images that exist on disk
    alarm_images: list[str] = []
    for rec in display_records:
        img = rec.get("alarm_image", "")
        if img and Path(img).exists():
            alarm_images.append(str(img))

    # Stats by alarm level
    level_counter = Counter(
        r.get("alarm_level", "UNKNOWN") for r in records
    )
    stats = dict(level_counter.most_common())

    return {
        "log_exists": True,
        "total": total,
        "filtered_count": filtered_count,
        "records": display_records,
        "alarm_images": alarm_images,
        "stats": stats,
    }


def export_log_csv(
    log_path: str = "data/logs/event_log.csv",
    output_path: str = "data/reports/log_export.csv",
    alarm_level: str = "ALL",
    event_type: str = "ALL",
    start_date: str = "",
    end_date: str = "",
) -> str:
    """Export filtered event log records to a CSV file for download.

    Args:
        log_path:      Path to the source CSV log file.
        output_path:   Path for the exported CSV file.
        alarm_level:   Filter by alarm level (ALL, HIGH, MEDIUM, LOW).
        event_type:    Filter by class_name (ALL, fire, smoke, no_helmet, no_vest).
        start_date:    Start date filter (YYYY-MM-DD), empty = no lower bound.
        end_date:      End date filter (YYYY-MM-DD), empty = no upper bound.

    Returns:
        The output file path (str). Returns empty string if source log not found.
    """
    log_path_obj = Path(log_path)

    if not log_path_obj.exists():
        return ""

    # Use query_event_log_filtered to get filtered records
    result = query_event_log_filtered(
        log_path=log_path,
        alarm_level=alarm_level,
        event_type=event_type,
        start_date=start_date,
        end_date=end_date,
        recent_n=999999,  # export all filtered, not just recent
    )

    if not result.get("log_exists") or not result.get("records"):
        return ""

    # Write filtered records to output CSV
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = result["records"][0].keys() if result["records"] else []
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(result["records"])

    return str(out_path)


def build_summary_markdown(result: dict) -> str:
    """Turn a query_event_log result into a Markdown string."""
    if not result.get("log_exists"):
        return f"*{result.get('error', 'No log available.')}*"

    lines = [
        f"**Total events**: {result['total_events']}",
        f"**Total alarms**: {result['total_alarms']}",
        "",
    ]

    # by task type
    by_task = result.get("by_task_type", {})
    if by_task:
        lines.append("**By task type**:")
        for task, count in by_task.items():
            lines.append(f"  - `{task}`: {count}")
        lines.append("")

    # by class name (top 10)
    by_class = result.get("by_class_name", {})
    if by_class:
        lines.append("**By class name (top 10)**:")
        for cls, count in list(by_class.items())[:10]:
            lines.append(f"  - `{cls}`: {count}")
        if len(by_class) > 10:
            lines.append(f"  - ... +{len(by_class) - 10} more")
        lines.append("")

    # by alarm level
    by_level = result.get("by_alarm_level", {})
    if by_level:
        lines.append("**By alarm level**:")
        for level, count in by_level.items():
            lines.append(f"  - `{level}`: {count}")
        lines.append("")

    # recent alarms
    recent = result.get("recent_alarms", [])
    if recent:
        lines.append(f"**Recent {len(recent)} alarms**:")
        for r in recent[:5]:
            reason = r.get("reason", "")
            lines.append(
                f"  - `{r.get('alarm_level', '?')}` "
                f"`{r.get('class_name', '?')}` "
                f"conf={r.get('confidence', '?')} "
                f"frame=#{r.get('frame_id', '?')}"
                + (f" -- {reason}" if reason else "")
            )
        lines.append("")

    # low confidence
    lc = result.get("low_confidence_count", 0)
    th = result.get("threshold", 0.3)
    lines.append(f"**Low-confidence events** (< {th}): {lc}")

    return "\n".join(lines)


def generate_inspection_report(
    log_path: str = "data/logs/event_log.csv",
    output_dir: str = str(REPORTS_DIR),
) -> dict:
    """Generate a full inspection report and save it as a Markdown file.

    Returns dict with:
        - log_exists: bool
        - error: str (if log not found)
        - report_markdown: str
        - report_path: str or None
        - alarm_images: list[str]
        - total_events, total_alarms: int
    """
    # ---- gather data ----
    data = query_event_log(log_path=log_path, recent_n=5, low_conf_threshold=LOW_CONF_THRESHOLD)

    if not data["log_exists"]:
        return {
            "log_exists": False,
            "error": data["error"],
            "report_markdown": f"*{data['error']}*",
            "report_path": None,
            "alarm_images": [],
            "total_events": 0,
            "total_alarms": 0,
        }

    # ---- collect alarm images ----
    alarm_images: list[str] = []
    for alarm in data["recent_alarms"]:
        img = alarm.get("alarm_image", "")
        if img and Path(img).exists():
            alarm_images.append(str(img))

    # ---- build markdown ----
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    ts_file = time.strftime("%Y%m%d_%H%M%S")

    lines = [
        "# RoboVision Agent \u2014 \u5de1\u68c0\u62a5\u544a",
        f"**\u751f\u6210\u65f6\u95f4**: {ts}",
        "",
        "---",
        "",
        "## \u6982\u89c8",
        "",
        "| \u6307\u6807 | \u6570\u503c |",
        "|------|------|",
        f"| \u603b\u4e8b\u4ef6\u6570 | {data['total_events']} |",
        f"| \u62a5\u8b66\u4e8b\u4ef6\u6570 | {data['total_alarms']} |",
        f"| \u4f4e\u7f6e\u4fe1\u5ea6\u4e8b\u4ef6 (< 0.3) | {data['low_confidence_count']} |",
        "",
    ]

    # by task_type
    by_task = data.get("by_task_type", {})
    if by_task:
        lines.append("## \u4efb\u52a1\u7c7b\u578b\u5206\u5e03")
        lines.append("")
        for task, count in by_task.items():
            lines.append(f"- `{task}`: {count}")
        lines.append("")

    # by class_name
    by_class = data.get("by_class_name", {})
    if by_class:
        lines.append("## \u68c0\u6d4b\u7c7b\u522b TOP 10")
        lines.append("")
        for cls, count in list(by_class.items())[:10]:
            lines.append(f"- `{cls}`: {count}")
        if len(by_class) > 10:
            lines.append(f"- ... \u5176\u4ed6 {len(by_class) - 10} \u7c7b")
        lines.append("")

    # by alarm_level
    by_level = data.get("by_alarm_level", {})
    if by_level:
        lines.append("## \u62a5\u8b66\u7b49\u7ea7\u5206\u5e03")
        lines.append("")
        for level, count in by_level.items():
            lines.append(f"- `{level}`: {count}")
        lines.append("")

    # recent 5 alarms
    recent = data.get("recent_alarms", [])
    if recent:
        lines.append("## \u6700\u8fd1 5 \u6761\u62a5\u8b66\u8be6\u60c5")
        lines.append("")
        for i, alarm in enumerate(recent, 1):
            reason = alarm.get("reason", "")
            lines.append(f"### \u62a5\u8b66 #{i}")
            lines.append(f"- **\u7b49\u7ea7**: `{alarm.get('alarm_level', '?')}`")
            lines.append(f"- **\u7c7b\u522b**: `{alarm.get('class_name', '?')}`")
            lines.append(f"- **\u7f6e\u4fe1\u5ea6**: {alarm.get('confidence', '?')}")
            lines.append(f"- **\u5e27\u53f7**: #{alarm.get('frame_id', '?')}")
            lines.append(f"- **\u65f6\u95f4**: {alarm.get('timestamp', '?')}")
            if reason:
                lines.append(f"- **\u539f\u56e0**: {reason}")
            img = alarm.get("alarm_image", "")
            if img and Path(img).exists():
                lines.append(f"- **\u622a\u56fe**: `{img}`")
            lines.append("")

    lines.append("---")
    lines.append(f"*\u62a5\u544a\u7531 RoboVision Agent \u81ea\u52a8\u751f\u6210\u4e8e {ts}*")

    report_md = "\n".join(lines)

    # ---- save to file ----
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"inspection_report_{ts_file}.md"
    report_path.write_text(report_md, encoding="utf-8")

    return {
        "log_exists": True,
        "report_markdown": report_md,
        "report_path": str(report_path),
        "alarm_images": alarm_images,
        "total_events": data["total_events"],
        "total_alarms": data["total_alarms"],
    }
