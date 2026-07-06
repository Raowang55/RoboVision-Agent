"""Real report generation tool.

Generates an HTML inspection report with detection statistics,
alarm screenshots (base64-embedded), and AI-generated safety advice
via Qwen3-VL API.
"""

import csv
import json
import base64
import io
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# ---------------------------------------------------------------------------
# constants
# ---------------------------------------------------------------------------

REPORTS_DIR = Path("data/reports")
COLUMNS = [
    "timestamp", "task_type", "media_type", "source", "frame_id",
    "class_name", "confidence", "bbox", "is_alarm", "alarm_level",
    "event_type", "output_image", "alarm_image", "reason",
]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _image_to_base64(image_path: str, max_width: int = 300) -> str:
    """Convert an image file to a base64 data URI, resized to max_width."""
    try:
        from PIL import Image
        img = Image.open(image_path)
        if img.width > max_width:
            ratio = max_width / img.width
            img = img.resize((max_width, int(img.height * ratio)))
        buf = io.BytesIO()
        fmt = img.format or "JPEG"
        img.save(buf, format=fmt)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/{fmt.lower()};base64,{b64}"
    except Exception:
        return ""


def _read_log(log_path: str) -> list[dict]:
    """Read CSV log rows into a list of dicts."""
    path = Path(log_path)
    if not path.exists():
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def _compute_stats(rows: list[dict]) -> dict:
    """Compute per-class count and average confidence."""
    class_counts = defaultdict(int)
    class_confs = defaultdict(list)

    for row in rows:
        cls = row.get("class_name", "unknown")
        class_counts[cls] += 1
        try:
            conf = float(row.get("confidence", 0))
            class_confs[cls].append(conf)
        except (ValueError, TypeError):
            pass

    stats = []
    for cls in sorted(class_counts.keys()):
        confs = class_confs[cls]
        avg_conf = sum(confs) / len(confs) if confs else 0.0
        stats.append({
            "class_name": cls,
            "count": class_counts[cls],
            "avg_confidence": round(avg_conf, 4),
        })

    return {
        "stats": stats,
        "total_events": len(rows),
    }


def _get_alarm_images(rows: list[dict]) -> list[str]:
    """Extract unique, existing alarm_image paths from rows."""
    seen = set()
    images = []
    for row in rows:
        if row.get("is_alarm", "").lower() == "true":
            path = row.get("alarm_image", "") or row.get("output_image", "")
            if path and path not in seen:
                seen.add(path)
                if Path(path).exists():
                    images.append(path)
    return images


def _get_safety_advice(detection_results: list[dict]) -> str:
    """Call Qwen3-VL API for a ~50-char safety suggestion."""
    try:
        from app.llm.deepseek_client import chat

        summary = []
        for d in detection_results[:20]:
            summary.append({
                "class": d.get("class_name", "?"),
                "conf": d.get("confidence", 0),
            })

        prompt = (
            "根据以下检测结果，写出50字左右的安全建议：\n"
            + json.dumps(summary, ensure_ascii=False)
        )

        response = chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200,
        )

        if response.get("success"):
            return response["content"]
        return "无法生成建议（API 调用失败）"

    except Exception:
        return "无法生成建议（API 不可用）"


# ---------------------------------------------------------------------------
# HTML builder
# ---------------------------------------------------------------------------

def _build_html(
    generation_time: str,
    stats: dict,
    log_available: bool,
    log_path: str,
    images: list[str],
    safety_advice: str,
    detection_count: int,
) -> str:
    """Assemble the complete HTML report string."""

    # Convert images to base64 thumbnails
    img_tags = []
    for img_path in images[:12]:
        b64 = _image_to_base64(img_path)
        if b64:
            img_tags.append(
                f'<img src="{b64}" '
                f'style="max-width:280px; margin:4px; border:1px solid #ccc;" '
                f'alt="{Path(img_path).name}">'
            )

    img_section = (
        "\n".join(img_tags)
        if img_tags
        else "<p style='color:#999;'>无截图/p>"
    )

    # Build stats table rows
    table_rows = ""
    for s in stats["stats"]:
        table_rows += f"""\
        <tr>
            <td>{s['class_name']}</td>
            <td>{s['count']}</td>
            <td>{s['avg_confidence']}</td>
        </tr>"""

    if not table_rows:
        table_rows = (
            '<tr><td colspan="3" style="color:#999;">无数据/td></tr>'
        )

    # Log availability note
    log_note = ""
    if not log_available:
        log_note = (
            f'<p class="warn" style="border-left-color:#e67e22;">'
            f'日志文件不存在：<code>{log_path}</code></p>'
        )

    year = datetime.now().year

    return f"""\
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>RoboVision Agent - 巡检报告</title>
<style>
  body {{
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    max-width: 900px; margin: 0 auto; padding: 24px;
    background: #f5f6fa; color: #2c3e50;
  }}
  h1 {{ border-bottom: 3px solid #3498db; padding-bottom: 8px; }}
  h2 {{ margin-top: 32px; color: #2980b9; }}
  table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
  th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
  th {{ background: #3498db; color: white; }}
  tr:nth-child(even) {{ background: #f9f9f9; }}
  .meta {{ color: #7f8c8d; font-size: 14px; }}
  .advice {{
    background: #eaf7ee; border-left: 4px solid #27ae60;
    padding: 12px 16px; margin: 16px 0;
  }}
  .warn {{
    background: #fdf2f2; border-left: 4px solid #e74c3c;
    padding: 12px 16px; margin: 16px 0;
  }}
  .images {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0; }}
  footer {{ margin-top: 40px; font-size: 12px; color: #bdc3c7; text-align: center; }}
</style>
</head>
<body>

<h1>RoboVision Agent 巡检报告</h1>
<p class="meta">
  生成时间：{generation_time}
  | 本次检测目标数：{detection_count}
  | 日志事件总数：{stats['total_events']}
</p>
{log_note}

<h2>检测统计/h2>
<table>
  <thead>
    <tr><th>类别</th><th>数量</th><th>平均置信度/th></tr>
  </thead>
  <tbody>
    {table_rows}
  </tbody>
</table>

<h2>报警 / 检测截图/h2>
<div class="images">
  {img_section}
</div>

<h2>安全建议</h2>
<div class="advice">
  <p>{safety_advice}</p>
</div>

<footer>
  RoboVision Agent &copy; {year} -- 自动生成，仅供参考</footer>

</body>
</html>"""


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------

def generate_report(
    detection_results: list[dict],
    log_path: str = "data/logs/event_log.csv",
) -> str:
    """Generate an HTML inspection report.

    Args:
        detection_results: List of detection dicts. Each dict should contain
            class_name, confidence, bbox, and optionally output_image_path.
        log_path: Path to the event log CSV file.

    Returns:
        Absolute path to the generated HTML report file.
    """
    # Ensure output directory exists
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Generate timestamped filename
    now = datetime.now()
    filename = f"report_{now.strftime('%Y%m%d_%H%M%S')}.html"
    output_path = REPORTS_DIR / filename

    # Read event log
    rows = _read_log(log_path)
    log_available = bool(rows)

    # Compute stats
    stats = _compute_stats(rows) if log_available else {
        "stats": [],
        "total_events": 0,
    }

    # Collect alarm images from log
    alarm_images = _get_alarm_images(rows) if log_available else []

    # Collect output images from detection_results
    detection_images = []
    for d in detection_results:
        img_path = (
            d.get("output_image_path")
            or d.get("output_image")
            or ""
        )
        if img_path and Path(img_path).exists():
            detection_images.append(img_path)

    # Merge and deduplicate
    all_images = detection_images + [
        p for p in alarm_images if p not in detection_images
    ]

    # Safety advice
    safety_advice = (
        _get_safety_advice(detection_results)
        if detection_results
        else "无检测数据，无法生成建议"
    )

    # Build and write HTML
    html = _build_html(
        generation_time=now.strftime("%Y-%m-%d %H:%M:%S"),
        stats=stats,
        log_available=log_available,
        log_path=log_path,
        images=all_images,
        safety_advice=safety_advice,
        detection_count=len(detection_results),
    )

    output_path.write_text(html, encoding="utf-8")
    return str(output_path.resolve())
