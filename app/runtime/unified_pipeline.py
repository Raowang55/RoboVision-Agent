"""Unified detection pipeline — routes to image, video, fire, or PPE.

Uses YOLO-World for open-vocabulary detection across all three tasks:
general detection, fire/smoke warning, and PPE safety inspection.
"""

import sys
import time
import csv
import json
from pathlib import Path

import cv2
import numpy as np

from ultralytics import YOLO, YOLOWorld

from app.config import YOLO_WORLD_MODEL, YOLO_WORLD_SMALL
from app.runtime.fire_alarm_rules import FireAlarmEngine
from app.tools.fire_log_tool import query_fire_log
from app.core.event_logger import append_event

# --- Color-based fire detection helper (fallback when YOLO-World misses fire/smoke) ---

def _detect_fire_by_color(frame_bgr, conf=0.3):
    """Detect fire regions using HSV colour segmentation (optimised).

    Falls back to colour heuristics when YOLO-World cannot detect fire/smoke.
    Returns a list of pseudo-detection dicts with class_name='fire'.
    """
    import numpy as np
    h, w = frame_bgr.shape[:2]
    # Downsample for speed (colour detection is resolution-tolerant)
    scale = max(1, min(w, h) // 320)
    small = cv2.resize(frame_bgr, (w // scale, h // scale))
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    # Fire colour ranges
    lower1 = np.array([0, 80, 120])
    upper1 = np.array([25, 255, 255])
    lower2 = np.array([160, 80, 120])
    upper2 = np.array([180, 255, 255])
    mask = cv2.bitwise_or(
        cv2.inRange(hsv, lower1, upper1),
        cv2.inRange(hsv, lower2, upper2),
    )
    # Quick check: skip expensive morphology if very few fire pixels
    fire_ratio = cv2.countNonZero(mask) / (mask.shape[0] * mask.shape[1])
    if fire_ratio < 0.01:
        return []
    # Morphological clean-up
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    # Find connected components
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
    detections = []
    min_area = int(mask.shape[0] * mask.shape[1] * 0.005)
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area < min_area:
            continue
        x1 = stats[i, cv2.CC_STAT_LEFT] * scale
        y1 = stats[i, cv2.CC_STAT_TOP] * scale
        x2 = (stats[i, cv2.CC_STAT_LEFT] + stats[i, cv2.CC_STAT_WIDTH]) * scale
        y2 = (stats[i, cv2.CC_STAT_TOP] + stats[i, cv2.CC_STAT_HEIGHT]) * scale
        box_area = (x2 - x1) * (y2 - y1)
        score = min(area / max(box_area / (scale * scale), 1) * 1.5, 0.95)
        if score < conf:
            continue
        detections.append({
            "class_id": -1,
            "class_name": "fire",
            "confidence": round(score, 3),
            "bbox": [round(float(x1), 1), round(float(y1), 1),
                     round(float(x2), 1), round(float(y2), 1)],
        })
    return detections

_WORLD_MODEL = None
_WORLD_MODEL_PATH = YOLO_WORLD_MODEL
_WORLD_MODEL_SMALL = YOLO_WORLD_SMALL

# Task to class names mapping
TASK_CLASSES = {
    "general": ["person", "car", "truck", "bus", "motorcycle", "bicycle",
                "traffic light", "stop sign", "fire hydrant", "bench",
                "bird", "cat", "dog", "backpack", "umbrella", "handbag",
                "suitcase", "bottle", "cup", "chair", "laptop", "cell phone"],
    "fire": ["fire", "smoke"],
    "ppe": ["person", "helmet", "hard-hat", "vest", "reflective-vest"],
}

# PPE-related classes (subset of ppe task classes)
PPE_CLASSES = {"person", "helmet", "hard-hat", "vest", "reflective-vest"}


def _get_world_model():
    """Lazy-load YOLO-World model (singleton), fall back to standard YOLO."""
    global _WORLD_MODEL
    if _WORLD_MODEL is not None:
        return _WORLD_MODEL, True

    if _WORLD_MODEL_PATH.exists():
        try:
            _WORLD_MODEL = YOLOWorld(str(_WORLD_MODEL_PATH))
            import logging
            logging.getLogger(__name__).info(f"YOLO-World loaded: {_WORLD_MODEL_PATH}")
            return _WORLD_MODEL, True
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"YOLO-World load failed: {e}")

    # Fallback to small model
    if _WORLD_MODEL_SMALL.exists():
        _WORLD_MODEL = YOLOWorld(str(_WORLD_MODEL_SMALL))
        import logging
        logging.getLogger(__name__).info(f"Fallback to small YOLO-World: {_WORLD_MODEL_SMALL}")
        return _WORLD_MODEL, True
    raise FileNotFoundError(f"No model found at {_WORLD_MODEL_PATH} or {_WORLD_MODEL_SMALL}")


def _set_task_classes(model, task: str, is_world: bool):
    """Set detection classes on the model for the given task."""
    if is_world:
        classes = TASK_CLASSES.get(task, TASK_CLASSES["general"])
        model.set_classes(classes)


# ── Detection functions ─────────────────────────────────────────────

def _detect_image(image_path: str, conf: float, task: str = "general") -> dict:
    """Run detection on a single image using YOLO-World."""
    model, is_world = _get_world_model()
    _set_task_classes(model, task, is_world)

    t0 = time.perf_counter()
    results = model(str(image_path), conf=conf, verbose=False)
    elapsed = (time.perf_counter() - t0) * 1000

    detections = []
    result = results[0]
    if result.boxes is not None:
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cls_id = int(box.cls[0].item())
            cls_name = result.names[cls_id]
            conf_val = round(box.conf[0].item(), 4)
            detections.append({
                "class_id": cls_id,
                "class_name": cls_name,
                "confidence": conf_val,
                "bbox": [round(x1, 1), round(y1, 1),
                         round(x2, 1), round(y2, 1)],
            })

    # Save annotated image
    output_dir = Path("data/outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    stem = Path(image_path).stem
    output_path = str(output_dir / f"{stem}_{task}_{ts}.jpg")

    annotated = result.plot()
    cv2.imwrite(output_path, annotated)

    class_counts = {}
    for d in detections:
        class_counts[d["class_name"]] = class_counts.get(d["class_name"], 0) + 1

    names_str = ", ".join(f"{c}:{n}" for c, n in sorted(class_counts.items(), key=lambda x: -x[1])[:8])
    message = f"Detected {len(detections)} object(s): {names_str} ({elapsed:.0f} ms)"

    return {
        "tool": "yolo_world",
        "model_path": str(_WORLD_MODEL_PATH),
        "output_image": output_path,
        "detections": detections,
        "latency_ms": round(elapsed, 1),
        "message": message,
        "class_counts": class_counts,
    }


def _detect_video(
    source: str | int,
    conf: float,
    frame_stride: int,
    max_frames: int,
    task: str,
) -> dict:
    """Run detection on a video file using YOLO-World."""
    model, is_world = _get_world_model()
    _set_task_classes(model, task, is_world)

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        return {
            "summary_md": f"**Error**: cannot open video source `{source}`.",
            "video_path": None,
            "log_path": None,
            "detections_json": {},
            "alarm_images": [],
        }

    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    source_name = Path(str(source)).name if isinstance(source, str) else f"camera_{source}"

    # Output paths
    out_dir = Path("data/outputs/videos").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    video_out = str(out_dir / f"{task}_{source_name}_{ts}.mp4")
    log_out = Path("data/logs").resolve() / f"{task}_{source_name}_{ts}.csv"
    log_out.parent.mkdir(parents=True, exist_ok=True)

    # Video writer
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(video_out, fourcc, fps / max(frame_stride, 1), (w, h))

    # CSV log
    csv_fh = open(log_out, "w", newline="", encoding="utf-8")
    csv_writer = csv.writer(csv_fh)
    csv_writer.writerow(["timestamp", "source", "frame_id", "class_name", "confidence", "bbox"])

    # Fire engine (only for fire task)
    alarm_engine = FireAlarmEngine(cooldown_seconds=5.0) if task == "fire" else None
    alarm_images = []

    # Fire alarm log CSV
    fire_log_path = Path("data/logs").resolve() / "fire_alarm_log.csv"
    fire_log_exists = fire_log_path.exists()
    fire_csv_fh = open(fire_log_path, "a", newline="", encoding="utf-8")
    fire_csv_writer = csv.writer(fire_csv_fh)
    if not fire_log_exists or fire_log_path.stat().st_size == 0:
        fire_csv_writer.writerow(["timestamp", "source", "frame_id", "event_type", "alarm_level", "class_name", "confidence", "bbox", "alarm_image", "reason"])

    # PPE counters
    ppe_violation_frames = 0
    total_person_frames = 0

    all_detections = []
    frame_id = 0
    processed = 0
    total_inference_ms = 0.0

    while True:
        ret, frame_bgr = cap.read()
        if not ret:
            break
        frame_id += 1

        if frame_id % frame_stride != 0:
            continue

        processed += 1
        if processed > max_frames:
            break

        # Inference
        t0 = time.perf_counter()
        results = model(frame_bgr, conf=conf, verbose=False)
        total_inference_ms += (time.perf_counter() - t0) * 1000

        annotated = frame_bgr.copy()
        frame_detections = []

        if results[0].boxes is not None:
            for box in results[0].boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                cls_id = int(box.cls[0].item())
                cls_name = results[0].names[cls_id]
                conf_val = round(box.conf[0].item(), 4)

                det = {
                    "class_id": cls_id,
                    "class_name": cls_name,
                    "confidence": conf_val,
                    "bbox": [round(x1, 1), round(y1, 1),
                             round(x2, 1), round(y2, 1)],
                }
                frame_detections.append(det)
                all_detections.append(det)

                # Colour: red for fire/smoke, orange for PPE violations, green for others
                if cls_name in ("fire", "smoke"):
                    colour = (0, 0, 255)
                elif cls_name in ("helmet", "hard-hat", "vest", "reflective-vest"):
                    colour = (0, 215, 255)
                else:
                    colour = (0, 255, 0)

                cv2.rectangle(annotated, (int(x1), int(y1)),
                              (int(x2), int(y2)), colour, 2)
                label = f"{cls_name} {conf_val:.2f}"
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                cv2.rectangle(annotated, (int(x1), int(y1) - th - 6),
                              (int(x1) + tw + 4, int(y1)), colour, -1)
                cv2.putText(annotated, label, (int(x1) + 2, int(y1) - 3),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Color-based fire detection fallback (when YOLO-World misses fire/smoke)
        if task == "fire" and alarm_engine is not None:
            has_fire_detection = any(
                d["class_name"] in ("fire", "smoke") for d in frame_detections
            )
            if not has_fire_detection:
                color_fire = _detect_fire_by_color(frame_bgr, conf=0.25)
                if color_fire:
                    frame_detections.extend(color_fire)
                    all_detections.extend(color_fire)

        # Fire alarm check
        if alarm_engine is not None:
            alarm = alarm_engine.update(frame_detections)
            if alarm is not None:
                alarm_ts = time.strftime("%Y%m%d_%H%M%S")
                alarm_fname = f"alarm_{alarm['alarm_level']}_{alarm_ts}.jpg"
                alarm_path = str(Path("data/alarms/fire").resolve() / alarm_fname)
                Path("data/alarms/fire").resolve().mkdir(parents=True, exist_ok=True)
                cv2.imwrite(alarm_path, annotated)
                alarm_images.append(alarm_path)

                # Write to fire alarm log CSV
                now_str = time.strftime("%Y-%m-%d %H:%M:%S")
                fire_csv_writer.writerow([
                    now_str, source_name, frame_id,
                    alarm["event_type"], alarm["alarm_level"],
                    alarm["class_name"], alarm["confidence"],
                    str(alarm["bbox"]), alarm_path, alarm["reason"],
                ])

                # Write to unified event log
                append_event({
                    "task_type": "fire",
                    "media_type": "video",
                    "source": source_name,
                    "frame_id": frame_id,
                    "class_name": alarm["class_name"],
                    "confidence": alarm["confidence"],
                    "bbox": alarm["bbox"],
                    "is_alarm": "True",
                    "alarm_level": alarm["alarm_level"],
                    "event_type": alarm["event_type"],
                    "alarm_image": alarm_path,
                    "reason": alarm["reason"],
                })

        # PPE violation check
        if task == "ppe":
            classes_in_frame = {d["class_name"] for d in frame_detections}
            has_person = "person" in classes_in_frame
            if has_person:
                total_person_frames += 1
                has_helmet = any(c in classes_in_frame for c in ("helmet", "hard-hat"))
                has_vest = any(c in classes_in_frame for c in ("vest", "reflective-vest"))
                if not has_helmet or not has_vest:
                    ppe_violation_frames += 1

        # CSV log
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        for d in frame_detections:
            csv_writer.writerow([
                now_str, source_name, frame_id,
                d["class_name"], d["confidence"], str(d["bbox"]),
            ])

            # Write fire/smoke detections to unified event log
            if task == "fire" and d["class_name"] in ("fire", "smoke"):
                append_event({
                    "task_type": "fire",
                    "media_type": "video",
                    "source": source_name,
                    "frame_id": frame_id,
                    "class_name": d["class_name"],
                    "confidence": d["confidence"],
                    "bbox": d["bbox"],
                    "is_alarm": "False",
                    "event_type": d["class_name"],
                })

        writer.write(annotated)

    # Cleanup
    cap.release()
    writer.release()
    csv_fh.close()
    fire_csv_fh.close()

    # Summary
    avg_ms = total_inference_ms / max(processed, 1)
    class_counts = {}
    for d in all_detections:
        class_counts[d["class_name"]] = class_counts.get(d["class_name"], 0) + 1

    lines = [
        f"**Task**: {task}",
        f"**Source**: {source_name}",
        f"**Frames processed**: {processed} (stride={frame_stride}, max={max_frames})",
        f"**Total detections**: {len(all_detections)}",
        f"**Avg inference**: {avg_ms:.0f} ms/frame",
        "",
        "**Per-class count**:",
    ]
    for cls, cnt in sorted(class_counts.items(), key=lambda x: -x[1])[:10]:
        lines.append(f"  - `{cls}`: {cnt}")
    if len(class_counts) > 10:
        lines.append(f"  - ... +{len(class_counts) - 10} more")

    if task == "fire":
        lines.append(f"\n**Alarms triggered**: {len(alarm_images)}")
        fire_log = query_fire_log()
        if fire_log.get("log_exists"):
            lines.append(f"**Fire alarm history**: {fire_log['total_alarms']} total")

    if task == "ppe":
        lines.append(f"\n**PPE Violation frames**: {ppe_violation_frames}/{total_person_frames}")
        if total_person_frames > 0:
            rate = ppe_violation_frames / total_person_frames * 100
            lines.append(f"**Violation rate**: {rate:.0f}%")

    lines.append(f"\n**Video saved**: `{video_out}`")
    lines.append(f"**Log saved**: `{log_out}`")

    return {
        "summary_md": "\n".join(lines),
        "video_path": video_out,
        "log_path": str(log_out),
        "detections_json": {
            "total": len(all_detections),
            "class_counts": class_counts,
            "detections": all_detections[:50],
        },
        "alarm_images": alarm_images,
    }


# ── Main entry point (called from Gradio) ───────────────────────────

def run_unified_detection(
    file_obj,
    text_prompt: str = "",
    task_dropdown: str = "自动判断",
    source_text: str = "",
    conf: float = 0.25,
    frame_stride: int = 5,
    max_frames: int = 300,
) -> tuple:
    """Unified detection entry point for the Gradio UI.

    Returns:
        (summary_md, annotated_image, video_path, alarm_gallery, json_str, log_path)
    """
    task = _parse_task(file_obj, text_prompt, task_dropdown)

    # Case 1: uploaded file
    if file_obj is not None:
        file_path = file_obj.name if hasattr(file_obj, "name") else str(file_obj)
        ext = Path(file_path).suffix.lower()

        if ext in (".jpg", ".jpeg", ".png", ".bmp", ".tiff"):
            # Image
            result = _detect_image(file_path, conf, task)
            summary = result.get("message", "Detection complete.")
            annotated = None
            out_img = result.get("output_image")
            if out_img and Path(out_img).exists():
                annotated = cv2.imread(out_img)
                annotated = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)

            return (
                f"**Task**: {task}\n\n**Result**: {summary}\n\n**Model**: YOLO-World",
                annotated,
                None,
                [],
                json.dumps(result.get("detections", []), ensure_ascii=False, indent=2),
                None,
            )

        else:
            # Video
            vid = _detect_video(file_path, conf, frame_stride, max_frames, task)
            return (
                vid["summary_md"],
                None,
                vid["video_path"],
                vid.get("alarm_images", []),
                json.dumps(vid["detections_json"], ensure_ascii=False, indent=2),
                vid["log_path"],
            )

    # Case 2: no file, use source_text
    if source_text.strip():
        if source_text.strip().isdigit():
            src = int(source_text.strip())
        else:
            src = source_text.strip()

        vid = _detect_video(src, conf, frame_stride, max_frames, task)
        return (
            vid["summary_md"],
            None,
            vid["video_path"],
            vid.get("alarm_images", []),
            json.dumps(vid["detections_json"], ensure_ascii=False, indent=2),
            vid["log_path"],
        )

    # Case 3: nothing provided
    return (
        "**请上传一个文件，或输入视频源地址。**",
        None, None, [], "{}", None,
    )


# ── Task parser ─────────────────────────────────────────────────────

def _parse_task(file_obj, text_prompt: str, task_dropdown: str) -> str:
    """Determine which pipeline to run.

    Returns one of: "general", "fire", "ppe"
    """
    if task_dropdown and task_dropdown != "自动判断":
        mapping = {
            "通用物品检测": "general",
            "General Object Detection": "general",
            "火灾烟雾预警": "fire",
            "Fire & Smoke Warning": "fire",
            "安全帽反光衣工检": "ppe",
            "PPE Safety Helmet & Reflective Vest Check": "ppe",
        }
        return mapping.get(task_dropdown, "general")

    # Auto-detect from text prompt
    text = text_prompt.lower()
    if any(w in text for w in ("fire", "smoke", "火灾", "火焰", "烟雾", "火", "烟")):
        return "fire"
    if any(w in text for w in ("安全帽", "反光衣", "ppe", "helmet", "vest", "头盔", "工服")):
        return "ppe"
    return "general"
