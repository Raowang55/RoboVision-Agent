你现在要基于我已有的 RoboVision 工业视觉报警项目，**将现有单Agent升级为多Agent协同系统**，新增「事件处置」模块作为第4个标签页。100%复用现有代码和技术栈，仅做增量改动。

---

## 一、现有项目精确接口（禁止臆造，必须严格按此调用）

### 1.1 LLM 调用
```python
from app.llm.deepseek_client import chat

# 签名
chat(messages: list[dict], temperature: float = 0.2, max_tokens: int = 1200) -> dict

# 返回
{"success": bool, "content": str, "model": str, "error": str | None}
# 必须传入 messages 列表，不可传纯字符串
```

### 1.2 RAG 检索（两个接口，任选其一）
```python
# 接口A：仅检索，返回原始 chunks
from app.rag.vector_store import search
search(question: str, top_k: int = 4) -> list[dict]
# 返回 [{"text": "...", "source": "文件名.md", "chunk_id": "..", "score": 0.89}, ...]

# 接口B：检索 + LLM 生成回答
from app.rag.rag_tool import rag_query
rag_query(question: str, top_k: int = 4, use_llm: bool = True, log_context: dict | None = None) -> dict
# 返回 {"answer": str, "retrieved_chunks": list[dict], "source_files": list[str], "used_llm": bool, "model": str}
```

### 1.3 知识库文档（`app/rag/knowledge_base/`，已索引）
- `fire_safety.md` — 火灾安全规范
- `ppe_rules.md` — PPE 佩戴规则
- `deployment_guide.md` — 部署指南
- `inspection_report.md` — 巡检报告模板
- `ops_troubleshoot.md` — 运维故障排查
- `project_manual.md` — 项目手册

### 1.4 视觉模型与报警
- 模型：`weights/yolov8m-worldv2.pt`（YOLOv8m-WorldV2）
- 报警引擎：`app/runtime/fire_alarm_rules.py` → `FireAlarmEngine`，输出 HIGH/MEDIUM/LOW 分级
- 检测流水线：`app/runtime/unified_pipeline.py` → `run_unified_detection()`
- 现有 Agent：`app/agent.py` → `run_agent()`

### 1.5 前端框架
- Gradio 6.18，`gr.Blocks()` 构建
- 深色工业控制台主题，CSS 变量：
  - `--bg-page: #0f172a` / `--bg-card: #1e293b` / `--bg-card-alt: #172033`
  - `--brand-blue: #2563eb` / `--text-primary: #e2e8f0` / `--text-secondary: #94a3b8`
  - `--radius-md: 12px` / `--shadow-card: 0 2px 6px rgba(0,0,0,.35)`
- 字体：`"Inter", "Noto Sans SC", system-ui, sans-serif`
- 卡片类：`section-card`（主卡）、`section-card-alt`（副卡）
- 按钮类：`primary-btn`（品牌蓝按钮）
- 容器宽度：`max-width: 76vw; min-width: 960px`，居中
- 现有3个标签页：视觉检测 / RAG知识问答 / 日志与报告

### 1.6 环境约束
- Python 3.13（`str | None` 语法可用）
- 禁止 `asyncio`，所有网络请求用 `requests` 同步
- 数据目录：`data/logs/`（CSV日志）、`data/alarms/fire/`（报警截图）、`data/outputs/videos/`（标注视频）

---

## 二、多Agent系统整体架构

```
┌─────────────────────────────────────────────────────────┐
│  RoboVision 多Agent 工业安全系统                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐   报警JSON    ┌──────────────────────┐ │
│  │ 检测Agent     │──────────────▶│ 处置多Agent子系统      │ │
│  │ (现有单Agent) │              │                      │ │
│  │              │              │ Supervisor → 分析     │ │
│  │ YOLO + 报警   │              │          → 检索预案   │ │
│  │ + RAG + 日志  │              │          → 派发指令   │ │
│  └──────────────┘              │          → 微信推送   │ │
│                                 └──────────────────────┘ │
│                                                         │
│  Tab1: 视觉检测  Tab2: RAG问答  Tab3: 日志  Tab4: 事件处置 │
└─────────────────────────────────────────────────────────┘
```

**5个Agent职责划分：**

| Agent | 类型 | 职责 | 输入 | 输出 |
|-------|------|------|------|------|
| 检测Agent | 现有（不改） | 图像/视频检测 + 报警 | 图片/视频/文本 | 报警JSON |
| Supervisor | 新增 | 校验 + 调度 + 汇总 | 报警JSON | 处置报告 |
| 事件分析 | 新增 | 事件画像（不给方案） | 报警JSON | 分析文本 |
| 预案检索 | 新增 | 查知识库匹配预案 | 事件类型+等级 | Top3预案 |
| 指令派发 | 新增 | 生成指令+推送+写库 | 分析+预案 | 工单+通知 |

---

## 三、新增模块详细规范

### 3.1 文件结构（全部增量，不动现有代码）
```
core/
├── __init__.py          # 空
├── agents.py            # 4个Agent的提示词 + LLM调用逻辑
├── graph.py             # DisposalState + LangGraph状态图 + run_disposal()
├── db.py                # SQLite建表 + 增查函数
└── mock.py              # 企业微信Webhook + 防抖降级 + Mock切换

ui/
├── __init__.py          # 空
└── disposal_tab.py      # build_disposal_tab(texts) -> gr.TabItem

disposal_demo.py         # 独立测试入口（USE_MOCK=True）
```

### 3.2 数据库设计（`core/db.py`）
```sql
-- 工单表
CREATE TABLE IF NOT EXISTS work_order (
    order_id    TEXT PRIMARY KEY,
    event_id    TEXT NOT NULL,
    event_type  TEXT NOT NULL,
    alarm_level TEXT NOT NULL,
    location    TEXT,
    analysis    TEXT,
    regulations TEXT,
    dispatch    TEXT,
    final_report TEXT,
    create_time TEXT NOT NULL,
    status      TEXT DEFAULT 'pending'
);

-- 流程日志表
CREATE TABLE IF NOT EXISTS disposal_log (
    log_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id    TEXT NOT NULL,
    step_name   TEXT NOT NULL,
    step_content TEXT,
    timestamp   TEXT NOT NULL
);
```
数据库文件：`data/work_order.db`，启动自动建表。封装函数：`insert_work_order()`, `insert_disposal_log()`, `query_orders_by_level()`, `query_orders_by_event()`。

### 3.3 企业微信推送（`core/mock.py`）
```python
WECHAT_WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=1a1d647a-cb26-495c-a6a5-d02f2e7e8108"
ALARM_COOLDOWN = 300  # 同位置同类报警5分钟内仅推送一次
USE_MOCK = False       # True时不发真实HTTP请求

def send_wechat_notification(event_type: str, alarm_level: str, location: str, summary: str) -> bool:
    """
    防抖：内存字典 _last_push_cache[(location, event_type)] = timestamp
    降级：推送失败仅打日志，不抛异常，不中断主流程
    Mock：USE_MOCK=True 时直接打印日志返回True
    消息格式：Markdown，颜色按等级：HIGH=#FF0000, MEDIUM=#FF8C00, LOW=#008000
    """
```

### 3.4 LangGraph 状态图（`core/graph.py`）
```python
class DisposalState(TypedDict):
    alarm_data: dict          # 输入报警JSON
    analysis: str             # 事件分析结果
    regulations: str          # 预案检索结果
    dispatch_result: dict     # 派发结果
    final_report: str         # 最终处置报告
    current_step: str         # 当前步骤名
    error_msg: str            # 错误信息

# 状态图链路
START → supervisor_judge → event_analysis → regulation_search
     → [条件：alarm_level=="HIGH" → emergency_linkage] → dispatch_order
     → final_summary → END

def run_disposal(alarm_json: dict) -> dict:
    """执行入口，返回 {"report": str, "order_id": str, "steps": list}"""
```

### 3.5 各Agent提示词要点（`core/agents.py`）

**Supervisor**：校验 event_id/event_type/alarm_level 必填 → 按等级分叉调度 → 汇总报告。字段缺失直接返回提示，不进入后续流程。

**事件分析Agent**：仅做画像，不给方案。LLM system prompt 要求输出：事件概况（1句）、风险等级确认、影响范围（结合location/bbox推导）、周边危险源提示（结合event_type推导）。禁止编造。

**预案检索Agent**：用 `rag_query()` 检索，query 自动拼接为 `"{location} {event_type} {alarm_level} 处置预案"`。输出 Top3 结果，保留 source_files 标识。

**指令派发Agent**：基于分析+预案，生成4角色指令（现场安全员/值班经理/消防中控/生产班组），每条格式：`【角色】动作 | 优先级 | 时限`。然后调用 `send_wechat_notification()` 推送，推送失败不影响指令生成。最后写入 work_order 表。

### 3.6 前端第4标签页（`ui/disposal_tab.py`）
```python
def build_disposal_tab(texts: dict) -> gr.TabItem:
    """返回 gr.TabItem("事件处置")，可直接嵌入现有 gr.Tabs()"""
```

**布局：左右分栏**（`gr.Row`，左 scale=4，右 scale=6）

**左栏（输入区）：**
1. `gr.Code(language="json")` — 报警JSON输入，支持粘贴
2. 「从示例导入」按钮 — 填充预设示例JSON
3. 报警等级显示框（`gr.Textbox`，HIGH红/MEDIUM橙/LOW黄高亮）
4. 「启动处置」按钮（`variant="primary", elem_classes="primary-btn"`）

**右栏（结果区）：**
1. 分步折叠面板（`gr.Accordion` 嵌套）：
   - Step 1: 事件分析 → 自动展开
   - Step 2: 预案检索
   - Step 3: 紧急联动（仅HIGH时显示）
   - Step 4: 指令派发
   - Step 5: 最终报告
2. 最终处置报告（`gr.Markdown`，`elem_classes="result-summary"`）
3. 工单JSON（`gr.JSON`）

**样式约束：**
- 完全复用现有 CSS 变量，不新增任何颜色/字体
- 卡片用 `elem_classes="section-card"` / `"section-card-alt"`
- 所有间距、圆角、阴影与现有三页一致
- 4个标签页切换时宽度不变，无跳动

### 3.7 前后端联动
- 主入口 `app/main.py` 中 `build_ui()` 新增导入和 TabItem
- 处置按钮 `click` 绑定 `run_disposal()`，输入报警JSON，输出报告+工单
- 不影响现有3个标签页的任何逻辑

---

## 四、需要修复的现有问题

在新增多Agent模块的同时，修复以下问题：

1. **YOLO 加载提示不消失**：`app/main.py` 中 `YOLO_STATUS_MD` 初始化为加载中状态，但线程加载完成后静态变量更新了，Gradio 未感知。需要改为用 `gr.Markdown` 的 `every` 定时轮询或 `gr.State` 传递状态。

2. **标签页切换宽度跳动**：4个标签页的内部 `gr.Row`/`gr.Column` 需要统一 `scale` 比例和 `min_width`，确保切换时不跳动。建议所有标签页主内容区统一使用 `gr.Row(equal_height=True)` 包裹。

3. **报警/Alarms 无显示**：检查 `process()` 函数中 `alarm_images` 的提取逻辑，确保 `run_unified_detection()` 返回的 alarms 字段正确传递到 `gr.Gallery`。

---

## 五、交付标准

1. 所有代码放在 `core/`、`ui/` 目录下，现有文件零改动（除 `app/main.py` 仅新增一个 TabItem 导入和注册）
2. `disposal_demo.py` 可独立运行，默认 `USE_MOCK = True`
3. 额外的 pip 依赖：`langgraph`, `langchain`, `requests`（前两个需安装，`requests` 项目已有）
4. 所有函数加类型标注，关键逻辑加注释
5. 中文界面，英文兼容（`texts` 字典同时提供 zh/en）
6. 推送失败不阻塞，数据库写入失败打日志并降级
