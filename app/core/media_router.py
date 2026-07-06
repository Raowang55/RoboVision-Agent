"""Media router -- unified dispatcher for image / video / camera detection.

Routes to the appropriate pipeline based on media type and task.
"""

import sys
import time
import json
import csv
from pathlib import Path

import cv2

from app.core.event_logger import append_event

from app.config import YOLO_WORLD_MODEL, YOLO_WORLD_SMALL

# ---------------------------------------------------------------------------
# constants
# ---------------------------------------------------------------------------

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}
VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}

FIRE_KEYWORDS = ["\u706b\u707e", "\u706b\u7130", "\u70df\u96fe",
                 "fire", "smoke", "\u706b", "\u70df"]
PPE_KEYWORDS  = ["\u5b89\u5168\u5e3d", "\u53cd\u5149\u8863", "ppe",
                 "helmet", "vest", "\u8fdd\u89c4", "\u5934\u76d4",
                 "\u5de5\u670d"]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _detect_media_type(
    input_path: str | None = None,
    source: str | None = None,
) -> str:
    if input_path:
        ext = Path(input_path).suffix.lower()
        if ext in IMAGE_EXTS:
            return "image"
        if ext in VIDEO_EXTS:
            return "video"
        return "image"

    if source:
        s = source.strip()
        if s.isdigit():
            return "camera"
        if s.startswith("rtsp://") or s.startswith("rtmp://"):
            return "camera"
        ext = Path(s).suffix.lower()
        if ext in VIDEO_EXTS:
            return "video"
        return "video"

    return "image"


def _detect_task_type(
    instruction: str = "",
    task_type: str = "auto",
) -> str:
    if task_type and task_type != "auto":
        return task_type
    text = instruction.lower()
    if any(w in text for w in FIRE_KEYWORDS):
        return "fire"
    if any(w in text for w in PPE_KEYWORDS):
        return "ppe"
    return "general"


def _resolve_model(task_type: str) -> Path:
    if task_type == "fire":
        candidates = [
            Path("weights/fire_smoke_yolo26n.pt"),
            YOLO_WORLD_SMALL,
        ]
    elif task_type == "ppe":
        candidates = [
            Path("weights/ppe_yolo26n.pt"),
            YOLO_WORLD_SMALL,
        ]
    else:
        candidates = [
            YOLO_WORLD_MODEL,
        ]
    for c in candidates:
        if c.exists():
            return c
    fallback = YOLO_WORLD_SMALL
    if fallback.exists():
        return fallback
    return candidates[0] if candidates else fallback


# ---------------------------------------------------------------------------
# image detection
# ---------------------------------------------------------------------------

def _detect_image(
    input_path: str,
    task_type: str,
    conf: float,
    source_name: str = "",
) -> dict:
    model_path = _resolve_model(task_type)
    if not model_path.exists():
        return {
            "output_image": None,
            "detections": [],
            "message": f"[Error] Model not found: {model_path}",
            "latency_ms": 0.0,
        }

    from ultralytics import YOLO

    model = YOLO(str(model_path))
    t0 = time.perf_counter()
    results = model(str(input_path), conf=conf, verbose=False)
    elapsed = (time.perf_counter() - t0) * 1000

    detections = []
    result = results[0]
    if result.boxes is not None:
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cls_id = int(box.cls[0].item())
            cls_name = result.names[cls_id]
            conf_val = round(box.conf[0].item(), 4)
            bbox_list = [round(x1, 1), round(y1, 1),
                         round(x2, 1), round(y2, 1)]
            detections.append({
                "class_id": cls_id,
                "class_name": cls_name,
                "confidence": conf_val,
                "bbox": bbox_list,
            })

    # Save annotated image
    output_dir = Path("data/outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    stem = Path(input_path).stem
    output_path = str(output_dir / f"{stem}_{task_type}_{ts}.jpg")

    annotated = result.plot()
    cv2.imwrite(output_path, annotated)

    if not detections:
        message = "No objects detected."
    else:
        names = sorted(set(d["class_name"] for d in detections))
        message = (
            f"Detected {len(detections)} object(s): "
            f"{', '.join(names)} ({elapsed:.0f} ms)"
        )

    # ---- unified event log ----
    for d in detections:
        cls = d["class_name"]
        is_fire_related = cls in ("fire", "smoke")
        append_event({
            "task_type": task_type,
            "media_type": "image",
            "source": source_name or Path(input_path).name,
            "frame_id": 0,
            "class_name": cls,
            "confidence": d["confidence"],
            "bbox": d["bbox"],
            "is_alarm": "True" if is_fire_related else "False",
            "alarm_level": "HIGH" if is_fire_related else "",
            "event_type": cls if is_fire_related else "detection",
            "output_image": output_path,
        })

    return {
        "output_image": output_path,
        "detections": detections,
        "message": message,
        "latency_ms": round(elapsed, 1),
    }


# ---------------------------------------------------------------------------
# video / camera detection
# ---------------------------------------------------------------------------

def _detect_video_or_camera(
    source: str | int,
    task_type: str,
    conf: float,
    frame_stride: int,
    max_frames: int,
) -> dict:
    model_path = _resolve_model(task_type)
    if not model_path.exists():
        return {
            "output_video": None,
            "detections": [],
            "alarm_images": [],
            "log_path": None,
            "message": f"[Error] Model not found: {model_path}",
        }

    from ultralytics import YOLO
    from app.runtime.fire_alarm_rules import FireAlarmEngine

    model = YOLO(str(model_path))

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        return {
            "output_video": None,
            "detections": [],
            "alarm_images": [],
            "log_path": None,
            "message": f"[Error] Cannot open source: {source}",
        }

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    source_name = (
        Path(str(source)).name
        if isinstance(source, str) else f"camera_{source}"
    )

    # Output paths
    out_dir = Path("data/outputs/videos")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    video_out = str(out_dir / f"{task_type}_{source_name}_{ts}.mp4")

    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_out = str(log_dir / f"{task_type}_{source_name}_{ts}.csv")

    csv_fh = open(log_out, "w", newline="", encoding="utf-8")
    csv_writer = csv.writer(csv_fh)
    csv_writer.writerow([
        "timestamp", "source", "frame_id", "class_name",
        "confidence", "bbox",
    ])

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    step = max(frame_stride, 1)
    writer = cv2.VideoWriter(video_out, fourcc, fps / step, (w, h))

    alarm_engine = FireAlarmEngine(cooldown_seconds=5.0) if task_type == "fire" else None
    alarm_images: list[str] = []

    all_detections = []
    frame_id = 0
    processed = 0

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

        results = model(frame_bgr, conf=conf, verbose=False)
        annotated = frame_bgr.copy()
        frame_detections = []

        if results[0].boxes is not None:
            for box in results[0].boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                cls_id = int(box.cls[0].item())
                cls_name = results[0].names[cls_id]
                conf_val = round(box.conf[0].item(), 4)
                bbox_list = [round(x1, 1), round(y1, 1),
                             round(x2, 1), round(y2, 1)]

                det = {
                    "class_id": cls_id,
                    "class_name": cls_name,
                    "confidence": conf_val,
                    "bbox": bbox_list,
                }
                frame_detections.append(det)
                all_detections.append(det)

                colour = (0, 0, 255) if cls_name in ("fire", "smoke") else (0, 255, 0)
                cv2.rectangle(annotated, (int(x1), int(y1)),
                              (int(x2), int(y2)), colour, 2)
                label = f"{cls_name} {conf_val:.2f}"
                (tw, th), _ = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                cv2.rectangle(annotated, (int(x1), int(y1) - th - 6),
                              (int(x1) + tw + 4, int(y1)), colour, -1)
                cv2.putText(annotated, label, (int(x1) + 2, int(y1) - 3),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Fire alarm check
        if alarm_engine is not None:
            alarm = alarm_engine.update(frame_detections)
            if alarm is not None:
                alarm_dir = Path("data/alarms/fire")
                alarm_dir.mkdir(parents=True, exist_ok=True)
                alarm_ts = time.strftime("%Y%m%d_%H%M%S")
                alarm_fname = f"alarm_{alarm['alarm_level']}_{alarm_ts}.jpg"
                alarm_path = str(alarm_dir / alarm_fname)
                cv2.imwrite(alarm_path, annotated)
                alarm_images.append(alarm_path)

                # ---- unified event log: alarm event ----
                append_event({
                    "task_type": task_type,
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

        # ---- unified event log: per-frame detections (every 10th to limit volume) ----
        if frame_id % max(frame_stride * 10, 1) == 0:
            for d in frame_detections:
                cls = d["class_name"]
                is_fire_class = cls in ("fire", "smoke")
                append_event({
                    "task_type": task_type,
                    "media_type": "video",
                    "source": source_name,
                    "frame_id": frame_id,
                    "class_name": cls,
                    "confidence": d["confidence"],
                    "bbox": d["bbox"],
                    "is_alarm": "False",
                    "event_type": cls if is_fire_class else "detection",
                })

        # Per-run CSV log (old format, kept for compatibility)
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        for d in frame_detections:
            csv_writer.writerow([
                now_str, source_name, frame_id,
                d["class_name"], d["confidence"], str(d["bbox"]),
            ])

        writer.write(annotated)

    cap.release()
    writer.release()
    csv_fh.close()

    # Summary
    class_counts = {}
    for d in all_detections:
        cls = d["class_name"]
        class_counts[cls] = class_counts.get(cls, 0) + 1

    top_classes = sorted(class_counts.items(), key=lambda x: -x[1])[:5]
    parts = [f"{cls}({cnt})" for cls, cnt in top_classes]

    msg = (
        f"Processed {processed} frames, "
        f"{len(all_detections)} detections. "
        f"Top: {', '.join(parts) if parts else 'none'}."
    )
    if task_type == "fire":
        msg += f" Alarms: {len(alarm_images)}."

    return {
        "output_video": video_out,
        "detections": all_detections,
        "alarm_images": alarm_images,
        "log_path": log_out,
        "message": msg,
    }


# ---------------------------------------------------------------------------
# main entry point
# ---------------------------------------------------------------------------

def detect_media(
    input_path: str | None = None,
    source: str | None = None,
    task_type: str = "auto",
    instruction: str = "",
    conf: float = 0.25,
    frame_stride: int = 5,
    max_frames: int = 300,
) -> dict:
    """Unified media detection entry point.

    Returns dict with keys:
        summary, output_image, output_video, alarm_images,
        detections, log_path, task_type, media_type
    """
    media_type = _detect_media_type(input_path, source)
    resolved_task = _detect_task_type(instruction, task_type)

    # ---- image ----
    if media_type == "image" and input_path:
        result = _detect_image(input_path, resolved_task, conf)
        return {
            "summary": result.get("message", "Done."),
            "output_image": result.get("output_image"),
            "output_video": None,
            "alarm_images": [],
            "detections": result.get("detections", []),
            "log_path": None,
            "task_type": resolved_task,
            "media_type": media_type,
        }

    # ---- video / camera ----
    if media_type in ("video", "camera"):
        src = source if media_type == "camera" else input_path
        if src is None:
            src = source or input_path
        if isinstance(src, str) and src.strip().isdigit():
            src = int(src.strip())

        result = _detect_video_or_camera(
            source=src,
            task_type=resolved_task,
            conf=conf,
            frame_stride=frame_stride,
            max_frames=max_frames,
        )
        return {
            "summary": result.get("message", "Done."),
            "output_image": None,
            "output_video": result.get("output_video"),
            "alarm_images": result.get("alarm_images", []),
            "detections": result.get("detections", []),
            "log_path": result.get("log_path"),
            "task_type": resolved_task,
            "media_type": media_type,
        }

    # ---- fallback ----
    return {
        "summary": "[Error] No input provided.",
        "output_image": None,
        "output_video": None,
        "alarm_images": [],
        "detections": [],
        "log_path": None,
        "task_type": resolved_task,
        "media_type": media_type,
    }
