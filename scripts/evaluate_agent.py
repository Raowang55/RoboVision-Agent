"""Offline evaluation for deterministic Agent routing and tool plans."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.agent import parse_intent, planned_tools

DEFAULT_CASES = PROJECT_ROOT / "tests" / "fixtures" / "agent_routing_eval.json"


def evaluate_cases(path: str | Path = DEFAULT_CASES) -> dict[str, Any]:
    """Evaluate intent accuracy, planned tool sequence, and routing latency."""
    cases = json.loads(Path(path).read_text(encoding="utf-8"))
    details = []
    durations = []
    route_hits = 0
    plan_hits = 0

    for case in cases:
        started = time.perf_counter()
        actual_intent = parse_intent(case["query"])
        actual_tools = planned_tools(actual_intent)
        duration_ms = (time.perf_counter() - started) * 1000
        durations.append(duration_ms)
        route_ok = actual_intent == case["expected_intent"]
        plan_ok = actual_tools == case["expected_tools"]
        route_hits += int(route_ok)
        plan_hits += int(plan_ok)
        details.append(
            {
                "id": case["id"],
                "route_ok": route_ok,
                "plan_ok": plan_ok,
                "expected_intent": case["expected_intent"],
                "actual_intent": actual_intent,
                "expected_tools": case["expected_tools"],
                "actual_tools": actual_tools,
                "duration_ms": round(duration_ms, 4),
            }
        )

    total = len(cases)
    sorted_durations = sorted(durations)
    p95_index = max(0, min(total - 1, int(total * 0.95) - 1)) if total else 0
    return {
        "total": total,
        "route_accuracy": route_hits / total if total else 0.0,
        "tool_sequence_pass_rate": plan_hits / total if total else 0.0,
        "average_routing_ms": round(statistics.mean(durations), 4) if durations else 0.0,
        "p95_routing_ms": round(sorted_durations[p95_index], 4) if durations else 0.0,
        "details": details,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate offline Agent routing")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="Evaluation JSON file")
    parser.add_argument("--json", action="store_true", help="Print full JSON details")
    args = parser.parse_args()
    result = evaluate_cases(args.cases)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("RoboVision Agent offline routing evaluation")
        print(f"  Cases: {result['total']}")
        print(f"  Route accuracy: {result['route_accuracy']:.1%}")
        print(f"  Tool sequence pass rate: {result['tool_sequence_pass_rate']:.1%}")
        print(f"  Average routing latency: {result['average_routing_ms']:.4f} ms")
        print(f"  P95 routing latency: {result['p95_routing_ms']:.4f} ms")

    if result["route_accuracy"] < 1.0 or result["tool_sequence_pass_rate"] < 1.0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
