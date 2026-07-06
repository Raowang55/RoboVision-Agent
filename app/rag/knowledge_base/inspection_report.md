# RoboVision-Agent Knowledge Base — 巡检报告生成规范

---

## 1. 报告类型

| 报告类型 | 触发方式 | 输出格式 | 保存路径 |
|----------|----------|----------|----------|
| 日常巡检报告 | Gradio "日志与报告" 标签页输入 "生成巡检报告" | Markdown (.md) | `data/reports/inspection_report_时间戳.md` |
| 火灾专项报告 | 输入 "火灾报警统计" 或 "fire log" | Markdown 摘要 | 前端实时展示 |
| PPE 合规报告 | 输入 "安全帽违规统计" | Markdown 摘要 | 前端实时展示 |

---

## 2. 统计维度

巡检报告自动从 `data/logs/event_log.csv` 读取数据，包含以下统计维度：

| 维度 | 说明 |
|------|------|
| 总事件数 | 日志中所有记录的条数 |
| 报警事件数 | is_alarm=True 的记录数 |
| 按 task_type 统计 | 通用检测 / 火灾预警 / PPE 巡检 分别计数 |
| 按 class_name 统计 | TOP 10 检测类别及数量 |
| 按 alarm_level 统计 | HIGH / MEDIUM / LOW 分别计数 |
| 最近 5 条报警详情 | 时间、等级、类别、置信度、帧号、原因 |
| 低置信度事件 | confidence < 0.3 的事件数 |

---

## 3. 报告输出规则

### 3.1 输出格式

报告以 Markdown 格式生成，包含：
- 一级标题：巡检报告
- 生成时间戳
- 概览表格（总事件数、报警事件数、低置信度事件数）
- 任务类型分布
- 检测类别 TOP 10
- 报警等级分布
- 最近 5 条报警详情（含截图路径）
- 页脚自动生成时间

### 3.2 调用入口

| 入口 | 方式 |
|------|------|
| Gradio 前端 | 在 "日志与报告" 标签页输入 "生成巡检报告" 或 "巡检报告" 或 "日报" |
| 代码调用 | `app/tools/event_log_tool.py` → `generate_inspection_report()` |
| Agent 调度 | 用户输入包含 "巡检报告、生成报告、日报、报告、summary" 时自动路由 |

---

## 4. 日志不存在时的处理

- 如果 `data/logs/event_log.csv` 不存在，返回友好提示：`Event log not found. Run detection or alarm monitoring first.`
- 不会报错崩溃

---

## 5. 与 RoboVision-Agent 系统联动

| 系统模块 | 功能 |
|----------|------|
| `event_logger.py` | 检测/报警时写入统一日志 |
| `event_log_tool.py` | 读取日志、统计、生成报告 |
| `agent.py` | 意图路由：关键词匹配 → 调用 `generate_inspection_report()` |
| `main.py` Gradio | 前端展示报告 Markdown + 报警截图 Gallery + 报告文件路径 |
