"""Fire / smoke alarm rule engine.

Decides alarm levels based on consecutive-frame persistence and
cooldown logic to avoid repeated alarms.
"""

import time


class FireAlarmEngine:
    """Tracks detection history and decides alarm level.

    Rules:
        - fire  confidence >= 0.5  for 3 consecutive frames → HIGH
        - smoke confidence >= 0.4  for 10 consecutive frames → MEDIUM
        - fire  AND  smoke appear together              → HIGH

    Cooldown prevents repeated alarms for the same event.
    """

    def __init__(self, cooldown_seconds: float = 5.0):
        self._cooldown = cooldown_seconds
        self._last_alarm_time = 0.0

        # ── Consecutive-frame counters ──────────────────────────────
        self._fire_frames  = 0   # consecutive frames with fire
        self._smoke_frames = 0   # consecutive frames with smoke

        # ── Thresholds ──────────────────────────────────────────────
        self.fire_conf_threshold  = 0.5
        self.smoke_conf_threshold = 0.4
        self.fire_min_frames      = 3
        self.smoke_min_frames     = 10

    def update(self, detections: list[dict]) -> dict | None:
        """Feed one frame's detections into the engine.

        Args:
            detections: list of detection dicts, each with
                        'class_name', 'confidence', 'bbox'.

        Returns:
            None if no alarm triggered.
            dict with keys event_type, alarm_level, class_name,
                         confidence, bbox, reason if alarm triggered.
        """
        has_fire  = any(
            d["class_name"] == "fire"
            and d["confidence"] >= self.fire_conf_threshold
            for d in detections
        )
        has_smoke = any(
            d["class_name"] == "smoke"
            and d["confidence"] >= self.smoke_conf_threshold
            for d in detections
        )

        # ── Update consecutive-frame counters ───────────────────────
        if has_fire:
            self._fire_frames += 1
        else:
            self._fire_frames = 0

        if has_smoke:
            self._smoke_frames += 1
        else:
            self._smoke_frames = 0

        # ── Decide alarm ────────────────────────────────────────────
        alarm = None

        # Rule 1: fire AND smoke together → HIGH
        if has_fire and has_smoke:
            alarm = self._build_alarm(
                "fire_and_smoke", "HIGH",
                detections,
                "Fire and smoke detected simultaneously",
            )

        # Rule 2: fire persists for 3+ frames → HIGH
        elif self._fire_frames >= self.fire_min_frames:
            alarm = self._build_alarm(
                "fire", "HIGH",
                detections,
                f"Fire detected for {self._fire_frames} consecutive frames",
            )

        # Rule 3: smoke persists for 10+ frames → MEDIUM
        elif self._smoke_frames >= self.smoke_min_frames:
            alarm = self._build_alarm(
                "smoke", "MEDIUM",
                detections,
                f"Smoke detected for {self._smoke_frames} consecutive frames",
            )

        # ── Cooldown check ──────────────────────────────────────────
        if alarm is not None:
            now = time.time()
            if now - self._last_alarm_time < self._cooldown:
                return None   # suppressed by cooldown
            self._last_alarm_time = now
            return alarm

        return None

    def _build_alarm(
        self,
        event_type: str,
        level: str,
        detections: list[dict],
        reason: str,
    ) -> dict:
        """Extract the best matching detection for the alarm."""
        target = "fire" if event_type == "fire" else "smoke"
        if event_type == "fire_and_smoke":
            target = "fire"  # prefer fire as primary

        best = max(
            (d for d in detections if d["class_name"] == target),
            key=lambda d: d["confidence"],
            default=None,
        )

        return {
            "event_type": event_type,
            "alarm_level": level,
            "class_name": target,
            "confidence": best["confidence"] if best else 0.0,
            "bbox": best["bbox"] if best else [0, 0, 0, 0],
            "reason": reason,
        }

    def reset(self):
        """Reset all counters (useful when switching sources)."""
        self._fire_frames = 0
        self._smoke_frames = 0
        self._last_alarm_time = 0.0
