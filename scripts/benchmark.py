"""Measure real Ultralytics inference latency for one image."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

import numpy as np
from ultralytics import YOLO, YOLOWorld


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark a YOLO model on an image")
    parser.add_argument("--model", required=True, help="Path to a .pt weight")
    parser.add_argument("--source", required=True, help="Path to an input image")
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--output", help="Optional JSON output path")
    args = parser.parse_args()

    model_path = Path(args.model)
    source_path = Path(args.source)
    if not model_path.exists() or not source_path.exists():
        raise SystemExit("Both --model and --source must exist")
    if args.iterations < 1 or args.warmup < 0:
        raise SystemExit("--iterations must be positive and --warmup cannot be negative")

    model_class = YOLOWorld if "world" in model_path.name.lower() else YOLO
    model = model_class(str(model_path))
    for _ in range(args.warmup):
        model.predict(str(source_path), device=args.device, verbose=False)

    samples: list[float] = []
    for _ in range(args.iterations):
        started = time.perf_counter()
        model.predict(str(source_path), device=args.device, verbose=False)
        samples.append((time.perf_counter() - started) * 1000)

    p50, p95 = np.percentile(samples, [50, 95]).tolist()
    mean_ms = statistics.fmean(samples)
    result = {
        "model": str(model_path),
        "source": str(source_path),
        "device": args.device,
        "iterations": args.iterations,
        "mean_ms": round(mean_ms, 2),
        "p50_ms": round(p50, 2),
        "p95_ms": round(p95, 2),
        "fps": round(1000.0 / mean_ms, 2),
    }
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
