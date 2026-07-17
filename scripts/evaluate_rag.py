"""Offline source-retrieval evaluation; no LLM judgement is used."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.rag.vector_store import search


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate RAG source Hit@K")
    parser.add_argument(
        "--cases",
        default="tests/fixtures/rag_eval.json",
        help="JSON file containing question and expected_source",
    )
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()
    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    hits = 0
    details = []
    for case in cases:
        results = search(case["question"], top_k=args.top_k)
        sources = [item["source"] for item in results]
        hit = case["expected_source"] in sources
        hits += int(hit)
        details.append({"question": case["question"], "hit": hit, "sources": sources})
    score = hits / len(cases) if cases else 0.0
    print(json.dumps({"hit_at_k": score, "top_k": args.top_k, "cases": details}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if score >= 0.8 else 1)


if __name__ == "__main__":
    main()
