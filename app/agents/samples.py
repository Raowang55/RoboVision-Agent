"""Static alarm examples used by the disposal UI and documentation."""

import json

SAMPLE_ALARM = json.dumps(
    {
        "event_id": "ALARM20260624001",
        "event_type": "fire",
        "alarm_level": "HIGH",
        "confidence": 0.92,
        "location": "3 号厂房焊接区",
        "timestamp": "2026-06-24 14:30:25",
        "image_path": "data/alarms/fire/alarm_HIGH_20260624_121834.jpg",
        "bbox": [320.5, 180.2, 540.8, 420.1],
        "reason": "连续 3 帧检测到火焰",
    },
    ensure_ascii=False,
    indent=2,
)

SAMPLE_ALARM_MEDIUM = json.dumps(
    {
        "event_id": "ALARM20260624002",
        "event_type": "smoke",
        "alarm_level": "MEDIUM",
        "confidence": 0.78,
        "location": "2 号厂房仓储区",
        "timestamp": "2026-06-24 15:10:33",
        "image_path": "data/alarms/smoke/alarm_MEDIUM_20260624_151033.jpg",
        "bbox": [150.2, 300.8, 420.6, 510.3],
        "reason": "货架附近检测到烟雾",
    },
    ensure_ascii=False,
    indent=2,
)

SAMPLE_ALARM_LOW = json.dumps(
    {
        "event_id": "ALARM20260624003",
        "event_type": "ppe_violation",
        "alarm_level": "LOW",
        "confidence": 0.65,
        "location": "1 号厂房装配线",
        "timestamp": "2026-06-24 16:45:12",
        "image_path": "data/alarms/ppe/alarm_LOW_20260624_164512.jpg",
        "bbox": [680.1, 210.5, 780.4, 580.9],
        "reason": "检测到未佩戴安全帽人员",
    },
    ensure_ascii=False,
    indent=2,
)
