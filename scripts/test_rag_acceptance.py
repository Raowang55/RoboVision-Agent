"""RAG acceptance test runner - 5 test queries."""
import sys
sys.path.insert(0, ".")

from app.rag.rag_tool import rag_query
from app.tools.event_log_tool import query_event_log

tests = [
    "检测到烟雾后应该怎么处理？",
    "为什么最近一次报警是 HIGH？",
    "安全帽违规应该如何分级？",
    "这个模型部署到 Jetson 需要注意什么？",
    "请根据最近一次报警生成一段巡检处置建议。",
]

results = []
for q in tests:
    print(f"=== Q: {q} ===")
    log_ctx = None
    if any(w in q for w in ("报警", "HIGH", "最近")):
        log_ctx = query_event_log()
        print(f"  log_context: total_events={log_ctx.get('total_events',0)}, alarms={log_ctx.get('total_alarms',0)}")

    r = rag_query(q, log_context=log_ctx, use_llm=True)
    print(f"  used_llm: {r['used_llm']}")
    print(f"  model: {r['model']}")
    print(f"  sources: {r['source_files']}")
    print(f"  answer_len: {len(r['answer'])}")
    print(f"  answer_preview: {r['answer'][:150]}...")
    print()
    results.append({
        "question": q,
        "used_llm": r["used_llm"],
        "model": r["model"],
        "sources": r["source_files"],
        "has_log": log_ctx is not None and log_ctx.get("log_exists", False),
        "answer_len": len(r["answer"]),
    })

print("=" * 60)
print("  ACCEPTANCE SUMMARY")
print("=" * 60)
all_pass = True
for i, r in enumerate(results):
    ok = (
        r["used_llm"]
        and r["model"] == "deepseek-v4-flash"
        and bool(r["sources"])
        and r["answer_len"] > 50
    )
    status = "PASS" if ok else "FAIL"
    if not ok:
        all_pass = False
    print(f"[{status}] {tests[i][:50]}")
    print(f"       llm={r['used_llm']}, model={r['model']}, sources={r['sources']}, log={r['has_log']}, len={r['answer_len']}")

print()
print("RESULT:", "ALL PASSED" if all_pass else "SOME FAILED")
