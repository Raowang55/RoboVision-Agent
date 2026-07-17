"""Run one reproducible detection-to-RAG-to-work-order demonstration."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.agent import run_agent
from app.agents.db import close_connection, configure_db, get_work_order, list_disposal_steps
from app.agents.graph import run_disposal
from app.config import DB_PATH
from scripts.doctor import collect_status


def _detection_classes(result: dict[str, Any]) -> list[str]:
    detection = result.get("detection", {})
    detections = detection.get("detections", detection.get("detections_json", {}).get("detections", []))
    return sorted(
        {
            str(item.get("class_name", item.get("class", "unknown")))
            for item in detections
        }
    )


def run_demo(
    image: str | Path,
    *,
    task: str = "general",
    use_llm: bool = False,
    send_notification: bool = False,
) -> dict[str, Any]:
    """Run the full demo with an isolated SQLite database."""
    image_path = Path(image).expanduser().resolve()
    if not image_path.is_file():
        raise FileNotFoundError(f"Demo image does not exist: {image_path}")

    started = time.perf_counter()
    prompt = "检测图中目标，然后查询对应的工业安全规范和处置建议"
    agent_response = run_agent(
        image=str(image_path),
        text_prompt=prompt,
        task=task,
        use_llm=use_llm,
    )
    if not agent_response["ok"]:
        raise RuntimeError(agent_response["error"] or "Agent chain failed")

    result = agent_response["result"]
    classes = _detection_classes(result)
    rag_result = result.get("rag", {})
    event_type = "fire" if "fire" in classes else "smoke" if "smoke" in classes else "inspection"
    alarm_level = "HIGH" if event_type == "fire" else "MEDIUM" if event_type == "smoke" else "LOW"
    alarm = {
        "event_id": f"DEMO-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "event_type": event_type,
        "alarm_level": alarm_level,
        "confidence": 1.0,
        "location": "离线演示区域",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "image_path": str(image_path),
        "reason": f"演示检测类别：{', '.join(classes) if classes else 'none'}",
    }

    original_db = DB_PATH
    with tempfile.TemporaryDirectory(prefix="robovision-demo-") as temp_dir:
        configure_db(Path(temp_dir) / "demo.db")
        try:
            disposal = run_disposal(alarm, send_notification=send_notification)
            order = get_work_order(disposal.get("order_id", ""))
            steps = list_disposal_steps(alarm["event_id"])
        finally:
            close_connection()
            configure_db(original_db)

    checks = {
        "agent_chain_ok": agent_response["intent"] == "chain" and len(agent_response["trace"]) == 2,
        "rag_has_sources": bool(rag_result.get("source_files")),
        "work_order_completed": bool(order and order.get("status") == "completed"),
        "workflow_steps_persisted": len(steps) >= 5,
        "external_notification_disabled": not send_notification or disposal.get("notification", False),
    }
    return {
        "ok": all(checks.values()),
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
        "environment": collect_status(),
        "agent": {
            "intent": agent_response["intent"],
            "planner_source": agent_response["planner_source"],
            "trace": agent_response["trace"],
            "classes": classes,
            "rag_sources": rag_result.get("source_files", []),
            "used_llm": bool(rag_result.get("used_llm")),
        },
        "work_order": order,
        "workflow_steps": steps,
        "notification_sent": disposal.get("notification", False),
        "checks": checks,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the RoboVision end-to-end demo")
    parser.add_argument("--image", required=True, help="Input image path")
    parser.add_argument("--task", choices=["general", "fire", "ppe"], default="general")
    parser.add_argument("--use-llm", action="store_true", help="Enable optional cloud answer generation")
    parser.add_argument(
        "--send-notification",
        action="store_true",
        help="Allow the configured Enterprise WeChat adapter to send",
    )
    parser.add_argument("--output", help="Optional JSON report path")
    args = parser.parse_args()

    report = run_demo(
        args.image,
        task=args.task,
        use_llm=args.use_llm,
        send_notification=args.send_notification,
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2, default=str)
    print(rendered)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
