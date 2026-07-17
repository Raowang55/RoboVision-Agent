# -*- coding: utf-8 -*-
"""Disposal workflow helper functions — shared by graph.py node functions.

Each function encapsulates one explicit step in the disposal workflow.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# supervisor_validate  --  validate alarm input and decide routing
# ---------------------------------------------------------------------------

def supervisor_validate(alarm_data: dict) -> dict:
    """Validate the alarm payload and return routing metadata."""
    if not isinstance(alarm_data, dict):
        return {"valid": False, "alarm_level": "UNKNOWN", "route": "ignore", "summary_instruction": "Invalid alarm data: expected JSON object, got " + type(alarm_data).__name__, "missing_fields": ["(invalid input)"]}

    required = ["event_id", "event_type", "alarm_level", "location", "timestamp"]
    missing = [f for f in required if f not in alarm_data or str(alarm_data.get(f, "")).strip() == ""]
    level = str(alarm_data.get("alarm_level", "")).strip().upper() or "UNKNOWN"
    supported_level = level in {"HIGH", "MEDIUM", "LOW"}
    if not supported_level and "alarm_level" not in missing:
        missing.append("alarm_level (must be HIGH, MEDIUM, or LOW)")

    return {
        "valid": len(missing) == 0 and supported_level,
        "alarm_level": level,
        "route": "disposal" if level in ("HIGH", "MEDIUM", "LOW") else "ignore",
        "summary_instruction": (
            f"Alarm validated. Level: {level}. Missing fields: {missing}."
            if missing
            else f"Alarm validated. Level: {level}. Routing to disposal."
        ),
        "missing_fields": missing,
    }
def run_analysis(alarm_data: dict) -> str:
    """Produce an analysis summary for the alarm event."""
    if not isinstance(alarm_data, dict):
        return "Invalid alarm data: expected a JSON object."
    event_type = alarm_data.get("event_type", "unknown")
    confidence = alarm_data.get("confidence", 0.0)
    location = alarm_data.get("location", "N/A")
    reason = alarm_data.get("reason", "")

    lines = [
        "## Event Analysis Report",
        "",
        f"- **Event Type**: {event_type}",
        f"- **Confidence**: {confidence:.2f}",
        f"- **Location**: {location}",
        f"- **Timestamp**: {alarm_data.get('timestamp', 'N/A')}",
    ]
    if reason:
        lines.append(f"- **Reason**: {reason}")

    lines.append("")
    lines.append(f"The {event_type} event at {location} was detected with "
                  f"confidence {confidence:.2f}. Further investigation may be required.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# run_regulation_search  --  look up matching regulations
# ---------------------------------------------------------------------------

def run_regulation_search(alarm_data: dict) -> dict:
    """Return matching regulation references for the alarm event.

    Returns a dict with:
        summary:       str  -- human-readable summary
        source_files:  list -- matched knowledge-base files
        chunks:        list -- relevant text snippets
    """
    if not isinstance(alarm_data, dict):
        return {"source_files": [], "chunks": [], "summary": "Invalid alarm data: expected a JSON object."}
    event_type = alarm_data.get("event_type", "general")

    regulation_map = {
        "fire": {
            "source_files": ["fire_safety.md"],
            "chunks": ["Fire safety regulation: immediate evacuation required."],
        },
        "smoke": {
            "source_files": ["fire_safety.md"],
            "chunks": ["Smoke alarm regulation: check sensor and evacuate."],
        },
        "ppe": {
            "source_files": ["ppe_rules.md"],
            "chunks": ["PPE regulation: hard hat and reflective vest required in risk zones."],
        },
        "ppe_violation": {
            "source_files": ["ppe_rules.md"],
            "chunks": ["PPE violation: verify explicit no-helmet or no-vest detections on site."],
        },
        "intrusion": {
            "source_files": ["ops_troubleshoot.md"],
            "chunks": ["Unauthorized entry detected. Dispatch security personnel."],
        },
    }

    match = regulation_map.get(event_type, {
        "source_files": ["fire_safety.md", "ppe_rules.md"],
        "chunks": ["General safety regulations apply."],
    })

    return {
        "summary": f"Matched {len(match['source_files'])} regulation source(s) for {event_type}.",
        "source_files": match["source_files"],
        "chunks": match["chunks"],
    }


# ---------------------------------------------------------------------------
# run_dispatch  --  generate dispatch instructions
# ---------------------------------------------------------------------------

def run_dispatch(alarm_data: dict, analysis: str, regulations: dict) -> str:
    """Generate dispatch instructions and work order content."""
    event_type = alarm_data.get("event_type", "unknown")
    level = alarm_data.get("alarm_level", "UNKNOWN").upper()
    location = alarm_data.get("location", "N/A")

    sources = regulations.get("source_files", [])

    lines = [
        "## Dispatch Order",
        "",
        f"- **Priority**: {level}",
        f"- **Event**: {event_type}",
        f"- **Location**: {location}",
        f"- **Applicable Regulations**: {', '.join(sources) if sources else 'General'}",
        "",
        f"Dispatch team to {location} to investigate {event_type} event. "
        f"Priority level: {level}.",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# run_final_summary  --  compose the final disposal report
# ---------------------------------------------------------------------------

def run_final_summary(
    alarm_data: dict,
    analysis: str,
    regulations: dict,
    dispatch: str,
    order_id: str = "N/A",
    notification_sent: bool = False,
) -> str:
    """Produce the final Markdown disposal report."""
    event_type = alarm_data.get("event_type", "unknown")
    level = alarm_data.get("alarm_level", "UNKNOWN").upper()
    location = alarm_data.get("location", "N/A")
    sources = regulations.get("source_files", [])

    lines = [
        "# Disposal Report",
        "",
        f"**Event**: {event_type}  |  **Level**: {level}  |  **Location**: {location}",
        f"**Work Order**: {order_id}  |  **Notification**: {'Sent' if notification_sent else 'Not Sent'}",
        "",
        "## Analysis",
        "",
        f"{analysis}",
        "",
        "## Regulations Referenced",
        "",
    ]
    for s in sources:
        lines.append(f"- {s}")
    lines.append("")
    lines.append("## Dispatch Instructions")
    lines.append("")
    lines.append(f"{dispatch}")

    return "\n".join(lines)
