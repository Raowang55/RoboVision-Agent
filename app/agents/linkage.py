"""Rule-based emergency linkage instructions for high-level alarms."""

from __future__ import annotations


def build_emergency_linkage_plan(alarm_data: dict) -> str:
    """Build an auditable action plan without claiming hardware execution."""
    event_type = str(alarm_data.get("event_type", "unknown"))
    location = str(alarm_data.get("location", "未知位置"))

    actions = [
        "通知现场安全负责人复核告警",
        "按现场应急预案启动声光告警和人员疏散",
        "隔离危险区域并保留告警截图与事件日志",
    ]
    if event_type in {"fire", "smoke"}:
        actions.extend(
            [
                "必要时拨打 119，并向消防人员说明告警位置",
                "按消防预案控制非消防电源和通风，避免擅自操作导致助燃",
            ]
        )
    elif event_type == "ppe_violation":
        actions.append("通知作业人员停止进入危险区域并补齐个人防护装备")

    action_lines = "\n".join(f"{index}. {action}" for index, action in enumerate(actions, 1))
    return (
        "**规则化应急联动方案**\n\n"
        f"- **事件类型**：{event_type}\n"
        f"- **位置**：{location}\n"
        f"- **建议动作**：\n{action_lines}\n"
        "- **执行状态**：已生成指令，须由现场人员或已接入的控制系统确认执行"
    )
