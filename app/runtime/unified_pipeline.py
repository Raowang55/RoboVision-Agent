# -*- coding: utf-8 -*-
"""Unified detection pipeline — routes to image, video, fire, or PPE.

Uses YOLO-World for open-vocabulary detection across all three tasks:
general detection, fire/smoke warning, and PPE safety inspection.
"""

import csv
import json
import pathlib
import subprocess
import threading
import time
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLOWorld

from app.config import (
    ALARM_COOLDOWN_SECONDS,
    DEFAULT_CONFIDENCE,
    ENABLE_HSV_FIRE_FALLBACK,
    FIRE_SMOKE_MODEL,
    LOG_DIR,
    OUTPUT_DIR,
    YOLO_WORLD_MODEL,
    YOLO_WORLD_SMALL,
)
from app.core.event_logger import append_event
from app.runtime.fire_alarm_rules import FireAlarmEngine
from app.tools.fire_log_tool import query_fire_log
from app.utils.media_utils import resolve_model_path

# --- Color-based fire detection helper (fallback when YOLO-World misses fire/smoke) ---

def _detect_fire_by_color(frame_bgr, conf=DEFAULT_CONFIDENCE):
    """Detect fire regions using HSV colour segmentation (optimised).

    Falls back to colour heuristics when YOLO-World cannot detect fire/smoke.
    Returns a list of pseudo-detection dicts with class_name='fire'.
    """
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
            "confidence": round(float(score), 3),
            "bbox": [round(float(x1), 1), round(float(y1), 1),
                     round(float(x2), 1), round(float(y2), 1)],
        })
    return detections

_WORLD_MODEL = None
_TASK_MODELS = {}
_MODEL_LOCK = threading.RLock()
_ULTRALYTICS_PATCHED = False
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
PPE_VIOLATION_CLASSES = {"no-helmet", "no-vest"}

# Class name normalization maps (model output -> canonical form)
FIRE_CLASS_MAP = {
    "Fire": "fire", "fire": "fire",
    "smoke": "smoke", "Smoke": "smoke",
    # The local fire_smoke_v8.pt model often emits this class for visible smoke.
    # The weight contains an undocumented class named "default". Do not turn
    # it into a smoke alarm without provenance or calibration evidence.
    "default": "unclassified",
}
PPE_CLASS_MAP = {
    "Person": "person", "person": "person", "worker": "person",
    "Helmet": "helmet", "helmet": "helmet", "hard-hat": "helmet",
    "No-Helmet": "no-helmet", "no helmet": "no-helmet", "no_helmet": "no-helmet",
    "Vest": "vest", "vest": "vest", "Safety-Vest": "vest", "reflective-vest": "vest",
    "No-Vest": "no-vest", "no vest": "no-vest", "no_vest": "no-vest",
}

def _normalize_class(task: str, cls_name: str) -> str:
    if task == "fire":
        return FIRE_CLASS_MAP.get(cls_name, cls_name.lower())
    if task == "ppe":
        return PPE_CLASS_MAP.get(cls_name, cls_name.lower())
    return cls_name


def _has_explicit_ppe_violation(detections: list[dict]) -> bool:
    """Only explicit negative PPE classes count as violations."""
    return any(item.get("class_name") in PPE_VIOLATION_CLASSES for item in detections)


def _make_browser_playable_video(video_path: str) -> tuple[str, str | None]:
    """Convert OpenCV's MP4V output to a browser-compatible H.264 MP4.

    OpenCV's Windows writer commonly produces an FMP4/MP4V stream. Chromium
    does not reliably play that codec even though the filename is ``.mp4``.
    ``imageio-ffmpeg`` ships an FFmpeg binary with the Python dependency, so
    the UI does not depend on a manually configured system PATH.
    """
    source = Path(video_path)
    converted = source.with_name(f"{source.stem}_h264.mp4")
    try:
        import imageio_ffmpeg
    except ImportError:
        return video_path, "未安装 imageio-ffmpeg，视频保留为原始 MP4V 格式，浏览器可能无法播放。"

    try:
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        command = [
            ffmpeg,
            "-y",
            "-i",
            str(source),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(converted),
        ]
        completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=180)
        if completed.returncode != 0 or not converted.exists() or converted.stat().st_size == 0:
            detail = completed.stderr.strip().splitlines()[-1] if completed.stderr.strip() else "未知 FFmpeg 错误"
            return video_path, f"H.264 转码失败：{detail}"
        converted.replace(source)
        return str(source), None
    except (OSError, subprocess.SubprocessError) as exc:
        return video_path, f"H.264 转码失败：{exc}"
    finally:
        if converted.exists():
            converted.unlink(missing_ok=True)


def _ensure_ultralytics_patch() -> None:
    global _ULTRALYTICS_PATCHED
    if not _ULTRALYTICS_PATCHED:
        from app.utils.ultralytics_patch import patch_ultralytics

        patch_ultralytics()
        _ULTRALYTICS_PATCHED = True


def _get_world_model():
    """Lazy-load the default YOLO-World model (singleton)."""
    global _WORLD_MODEL
    _ensure_ultralytics_patch()
    if _WORLD_MODEL is not None:
        return _WORLD_MODEL, True

    with _MODEL_LOCK:
        if _WORLD_MODEL is not None:
            return _WORLD_MODEL, True
        if _WORLD_MODEL_PATH.exists():
            try:
                _WORLD_MODEL = YOLOWorld(str(_WORLD_MODEL_PATH))
                import logging
                logging.getLogger(__name__).info("YOLO-World loaded: %s", _WORLD_MODEL_PATH)
                return _WORLD_MODEL, True
            except Exception as exc:
                import logging
                logging.getLogger(__name__).warning("YOLO-World load failed: %s", exc)

        if _WORLD_MODEL_SMALL.exists():
            _WORLD_MODEL = YOLOWorld(str(_WORLD_MODEL_SMALL))
            import logging
            logging.getLogger(__name__).info("Fallback to small YOLO-World: %s", _WORLD_MODEL_SMALL)
            return _WORLD_MODEL, True
    raise FileNotFoundError(f"No model found at {_WORLD_MODEL_PATH} or {_WORLD_MODEL_SMALL}")


def _get_model_for_task(task: str):
    """Load the best model for a given task.

    For general tasks: YOLO-World with open-vocabulary set_classes.
    For fire/smoke: YOLO-World set_classes(["fire","smoke"]) is used
    as the primary detector (better generalization than small task models).
    HSV color fallback in _detect_video catches what YOLO-World misses.
    For PPE: task-specific model first, YOLO-World fallback.

    Returns:
        (model, is_yolo_world) — is_yolo_world=True means set_classes is needed.
    """
    _ensure_ultralytics_patch()
    import logging
    log = logging.getLogger(__name__)

    if task in _TASK_MODELS:
        return _TASK_MODELS[task]

    # For fire detection: prefer the task-specific smoke/fire model, then fall back
    # to YOLO-World if the local weight is unavailable.
    if task == "fire":
        if FIRE_SMOKE_MODEL.exists():
            from ultralytics import YOLO
            log.info(f"Loading task-specific fire/smoke model: {FIRE_SMOKE_MODEL}")
            loaded = (YOLO(str(FIRE_SMOKE_MODEL)), False)
            _TASK_MODELS[task] = loaded
            return loaded
        model, _ = _get_world_model()
        _set_task_classes(model, task, True)
        return model, True

    # For PPE: try task-specific model first
    if task == "ppe":
        model_path = resolve_model_path(task)
        is_ppe_specific = model_path.name == "ppe_v8.pt"
        if is_ppe_specific and model_path.exists():
            from ultralytics import YOLO
            log.info(f"Loading task-specific PPE model: {model_path}")
            loaded = (YOLO(str(model_path)), False)
            _TASK_MODELS[task] = loaded
            return loaded

    # Default: YOLO-World
    model, _ = _get_world_model()
    _set_task_classes(model, task, True)
    return model, True


def _set_task_classes(model, task: str, is_world: bool):
    """Set detection classes on the model for the given task."""
    if is_world:
        classes = TASK_CLASSES.get(task, TASK_CLASSES["general"])
        model.set_classes(classes)


def _model_path_for_task(task: str) -> Path:
    """Return the configured model path that should be reported for a task."""
    if task == "fire" and FIRE_SMOKE_MODEL.exists():
        return FIRE_SMOKE_MODEL
    if task == "ppe":
        return resolve_model_path(task)
    return _WORLD_MODEL_PATH


# ── Detection functions ─────────────────────────────────────────────

def _detect_image(image_path: str, conf: float, task: str = "general") -> dict:
    """Run detection on a single image using the best available model."""
    model, is_world = _get_model_for_task(task)
    model_path = _model_path_for_task(task)

    # Resolve path for Windows compatibility with special characters
    image_path = str(pathlib.Path(image_path).resolve())
    t0 = time.perf_counter()
    results = model(image_path, conf=conf, verbose=False)
    elapsed = (time.perf_counter() - t0) * 1000

    detections = []
    result = results[0]
    if result.boxes is not None:
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cls_id = int(box.cls[0].item())
            cls_name = result.names[cls_id]
            normalized = _normalize_class(task, cls_name)
            if not normalized:
                continue
            conf_val = round(box.conf[0].item(), 4)
            detections.append({
            "class_id": cls_id,
            "class_name": normalized,
            "confidence": conf_val,
                "bbox": [round(x1, 1), round(y1, 1),
                         round(x2, 1), round(y2, 1)],
            })

    # Save annotated image
    output_dir = OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    stem = Path(image_path).stem
    output_path = str(output_dir / f"{stem}_{task}_{ts}.jpg")

    annotated = cv2.imread(image_path)
    if annotated is None:
        annotated = result.plot()
    else:
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            colour = (0, 0, 255) if det["class_name"] in ("fire", "smoke") else (0, 255, 0)
            cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), colour, 2)
            label = f"{det['class_name']} {det['confidence']:.2f}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            y_text = max(int(y1), th + 8)
            cv2.rectangle(
                annotated,
                (int(x1), y_text - th - 8),
                (int(x1) + tw + 6, y_text),
                colour,
                -1,
            )
            cv2.putText(
                annotated,
                label,
                (int(x1) + 3, y_text - 4),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )
    cv2.imwrite(output_path, annotated)

    class_counts = {}
    for d in detections:
        class_counts[d["class_name"]] = class_counts.get(d["class_name"], 0) + 1

    ppe_violations = [
        detection
        for detection in detections
        if detection["class_name"] in PPE_VIOLATION_CLASSES
    ]

    names_str = ", ".join(f"{c}:{n}" for c, n in sorted(class_counts.items(), key=lambda x: -x[1])[:8])
    message = f"Detected {len(detections)} object(s): {names_str} ({elapsed:.0f} ms)"

    return {
        "tool": "yolo_world" if is_world else "yolo_task_model",
        "model_path": str(model_path),
        "output_image": output_path,
        "detections": detections,
        "latency_ms": round(elapsed, 1),
        "message": message,
        "class_counts": class_counts,
        "ppe_violations": ppe_violations if task == "ppe" else [],
    }


def _detect_video(
    source: str | int,
    conf: float,
    frame_stride: int,
    max_frames: int,
    task: str,
) -> dict:
    """Run detection on a video file using YOLO-World."""
    frame_stride = max(int(frame_stride), 1)
    max_frames = max(int(max_frames), 1)
    # On Windows, cv2.VideoCapture may fail with paths containing special chars.
    # Convert to absolute path and use forward slashes for better compatibility.
    if isinstance(source, str):
        source = str(pathlib.Path(source).resolve())
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        return {
            "summary_md": f"**Error**: cannot open video source `{source}`.",
            "video_path": None,
            "log_path": None,
            "detections_json": {},
            "alarm_images": [],
        }

    model, is_world = _get_model_for_task(task)

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = 25.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    source_name = Path(str(source)).name if isinstance(source, str) else f"camera_{source}"

    # Output paths
    out_dir = (OUTPUT_DIR / "videos").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    video_out = str(out_dir / f"{task}_{source_name}_{ts}.mp4")
    log_out = LOG_DIR.resolve() / f"{task}_{source_name}_{ts}.csv"
    log_out.parent.mkdir(parents=True, exist_ok=True)

    # Video writer
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(video_out, fourcc, fps / max(frame_stride, 1), (w, h))

    # CSV log
    csv_fh = open(log_out, "w", newline="", encoding="utf-8")
    csv_writer = csv.writer(csv_fh)
    csv_writer.writerow(["timestamp", "source", "frame_id", "class_name", "confidence", "bbox"])

    # Fire engine (only for fire task)
    alarm_engine = FireAlarmEngine(cooldown_seconds=ALARM_COOLDOWN_SECONDS) if task == "fire" else None
    alarm_images = []

    # Fire alarm log CSV
    fire_csv_fh = None
    fire_csv_writer = None
    if task == "fire":
        fire_log_path = LOG_DIR.resolve() / "fire_alarm_log.csv"
        fire_log_exists = fire_log_path.exists()
        fire_csv_fh = open(fire_log_path, "a", newline="", encoding="utf-8")
        fire_csv_writer = csv.writer(fire_csv_fh)
    if fire_csv_writer is not None and (not fire_log_exists or fire_log_path.stat().st_size == 0):
        fire_csv_writer.writerow([
        "timestamp", "source", "frame_id", "event_type",
        "alarm_level", "class_name", "confidence",
        "bbox", "alarm_image", "reason",
    ])

    # PPE counters
    ppe_violation_frames = 0
    total_person_frames = 0

    all_detections = []
    frame_id = 0
    processed = 0
    total_inference_ms = 0.0

    try:
        while True:
            ret, frame_bgr = cap.read()
            if not ret:
                break
            frame_id += 1

            if frame_id % frame_stride != 0:
                continue

            if processed >= max_frames:
                break
            processed += 1

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
                    normalized = _normalize_class(task, cls_name)
                    if not normalized:
                        continue
                    conf_val = round(box.conf[0].item(), 4)

                    det = {
                        "class_id": cls_id,
                        "class_name": normalized,
                        "confidence": conf_val,
                        "bbox": [round(x1, 1), round(y1, 1),
                                 round(x2, 1), round(y2, 1)],
                    }
                    frame_detections.append(det)
                    all_detections.append(det)

                    # Colour: red for fire/smoke, orange for PPE, green for others.
                    if normalized in ("fire", "smoke"):
                        colour = (0, 0, 255)
                    elif normalized in ("helmet", "hard-hat", "vest", "reflective-vest"):
                        colour = (0, 215, 255)
                    else:
                        colour = (0, 255, 0)

                    cv2.rectangle(annotated, (int(x1), int(y1)),
                                  (int(x2), int(y2)), colour, 2)
                    label = f"{normalized} {conf_val:.2f}"
                    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                    cv2.rectangle(annotated, (int(x1), int(y1) - th - 6),
                                  (int(x1) + tw + 4, int(y1)), colour, -1)
                    cv2.putText(annotated, label, (int(x1) + 2, int(y1) - 3),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # Color-based fire fallback when the model misses fire/smoke.
            if task == "fire" and alarm_engine is not None and ENABLE_HSV_FIRE_FALLBACK:
                has_fire_detection = any(
                    d["class_name"] in ("fire", "smoke") for d in frame_detections
                )
                if not has_fire_detection:
                    color_fire = _detect_fire_by_color(frame_bgr, conf=0.25)
                    for d in color_fire:
                        x1, y1, x2, y2 = d["bbox"]
                        cv2.rectangle(annotated, (int(x1), int(y1)),
                                      (int(x2), int(y2)), (0, 0, 255), 2)
                        label = f"fire {d['confidence']:.2f}"
                        cv2.putText(annotated, label, (int(x1), max(int(y1) - 8, 20)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
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
                    if fire_csv_writer is not None:
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
                    if _has_explicit_ppe_violation(frame_detections):
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
    finally:
        try:
            cap.release()
        except Exception:
            pass
        try:
            writer.release()
        except Exception:
            pass
        try:
            csv_fh.close()
        except Exception:
            pass
        try:
            if fire_csv_fh is not None:
                fire_csv_fh.close()
        except Exception:
            pass

    video_out, video_warning = _make_browser_playable_video(video_out)

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
    if video_warning:
        lines.append(f"**Video warning**: {video_warning}")

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
        "video_warning": video_warning,
    }


# ── Main entry point (called from Gradio) ───────────────────────────

def run_unified_detection(
    file_obj,
    text_prompt: str = "",
    task_dropdown: str = "自动判断",
    source_text: str = "",
    conf: float = DEFAULT_CONFIDENCE,
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
                (
                    f"**Task**: {task}\n\n"
                    f"**Result**: {summary}\n\n"
                    f"**Model**: {Path(result.get('model_path', '')).name}"
                ),
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
