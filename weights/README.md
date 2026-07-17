# Model weights

Model binaries are intentionally not committed. Download the reproducible demo
weights with `python scripts/download_models.py`; the script verifies SHA-256
before replacing a local file.

- `yolov8s-worldv2.pt`: default YOLO-World general/open-vocabulary detector, downloaded from [Ultralytics assets v8.3.0](https://github.com/ultralytics/assets/releases/tag/v8.3.0) (SHA-256: `9b2c17ab6124a913e9b3a5c170617920d91b0f01111a8479da69f00e2cf27792`). `yolov8m-worldv2.pt` is an optional local override.
- `fire_smoke_yolov8n.pt`: default fire/smoke detector. It is the `best.pt` release from [luminous0219/fire-and-smoke-detection-yolov8](https://github.com/luminous0219/fire-and-smoke-detection-yolov8), downloaded on 2026-07-16 (SHA-256: `ac0a10257b2bc1f20c9d957f8adeeb61dd6140322fc19d0b4a116cb491776d16`). The upstream README describes a YOLOv8n model trained to detect `fire` and `smoke`; this project only integrates the third-party weight and does not claim its training or accuracy.
- `fire_smoke_v8.pt`: legacy optional fire/smoke detector. It is not the default because its emitted `default` class cannot be treated as a verified fire/smoke label.
- `ppe_v8.pt`: optional PPE detector; the current integration uses explicit `No-Helmet` and `No-Vest` classes for violation statistics. Its upstream source is not recorded, so it is deliberately not downloaded by the script and must not be described as a project-trained model.

Run `python scripts/doctor.py` to see which weights are available. When a task-specific weight is missing, the pipeline reports and uses YOLO-World as a lower-specialization fallback; it never returns synthetic detections.
