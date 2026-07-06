# RoboVision-Agent Knowledge Base — 项目手册

---

## 1. 项目概述

RoboVision-Agent 是一个工业视觉预警 Agent 控制台，面向安全生产场景，支持图片/视频/摄像头输入，集成 YOLO 目标检测、火灾烟雾预警、安全帽反光衣巡检、统一事件日志、巡检报告生成和 RAG 知识库问答。

**技术栈**：Python 3.13 + Gradio 4.x + Ultralytics YOLO + ChromaDB + BGE Embedding + DeepSeek API + OpenCV

---

## 2. 核心功能

### 2.1 YOLO 目标检测

- 使用 Ultralytics YOLO 模型（yolo26n.pt）
- 支持 COCO 80 类目标检测
- 接口：`app/tools/yolo_tool.py` → `detect(image_path, conf=0.25)`
- 返回检测框、类别、置信度、标注图片

### 2.2 火灾烟雾预警

- 检测 fire 和 smoke 类别
- 连续帧确认规则：fire 3 帧 / smoke 10 帧
- 报警分级：HIGH / MEDIUM / LOW
- 接口：`app/runtime/fire_video_detector.py` + `fire_alarm_rules.py`

### 2.3 安全帽反光衣巡检（PPE）

- YOLO 检测安全帽和反光衣佩戴情况
- 违规分级：严重违规 / 一般违规
- 接口：`app/runtime/ppe_pipeline.py`

### 2.4 统一事件日志

- 所有检测和报警事件写入 `data/logs/event_log.csv`
- 14 个字段：timestamp, task_type, media_type, source, frame_id, class_name, confidence, bbox, is_alarm, alarm_level, event_type, output_image, alarm_image, reason
- 接口：`app/core/event_logger.py` → `append_event(event)`

### 2.5 日志查询与巡检报告

- 查询总事件数、报警次数
- 按 task_type / class_name / alarm_level 统计
- 自动生成 Markdown 巡检报告，保存至 `data/reports/`
- 接口：`app/tools/event_log_tool.py`

### 2.6 RAG 知识库问答

- 知识库：fire_safety.md / ppe_rules.md / deployment_guide.md / project_manual.md
- Embedding：BAAI/bge-small-zh-v1.5 → ChromaDB 持久化
- 大模型：DeepSeek API (deepseek-v4-flash)
- 支持多轮对话记忆、API 失败兜底
- 接口：`app/rag/rag_tool.py` → `rag_query(question)`

### 2.7 Agent 智能调度

- LLM 意图解析（DeepSeek）+ 关键词兜底
- 自研 ReAct 循环：Think → Act → Observe
- 多步链式调用：检测 → 提取类别 → RAG 查询规范
- 接口：`app/agent.py` → `run_agent(image, text_prompt)`

---

## 3. 项目结构

```
app/
├── agent.py              # Agent 调度（意图路由 + ReAct 循环 + 链式调用）
├── main.py               # Gradio 前端（三标签页控制台 + 多语言切换）
├── core/
│   ├── event_logger.py   # 统一事件日志写入
│   └── media_router.py   # 媒体类型统一调度（图片/视频/摄像头）
├── runtime/
│   ├── video_detector.py       # 通用视频检测
│   ├── fire_video_detector.py  # 火灾视频检测
│   ├── fire_alarm_rules.py     # 报警规则引擎
│   ├── ppe_pipeline.py         # PPE 检测管线
│   └── unified_pipeline.py     # 统一检测管线
├── tools/
│   ├── yolo_tool.py       # YOLO 检测工具
│   ├── event_log_tool.py  # 事件日志查询 + 巡检报告生成
│   ├── fire_log_tool.py   # 火灾日志查询
│   └── report_tool.py     # HTML 报告生成
├── llm/
│   └── deepseek_client.py # DeepSeek API 客户端
├── rag/
│   ├── document_loader.py  # 文档加载与切块
│   ├── vector_store.py     # ChromaDB 向量存储
│   ├── prompt_builder.py   # RAG 提示词构建
│   └── rag_tool.py         # RAG 检索 + 生成
└── utils/
    ├── image_utils.py      # 图像处理
    ├── vis_utils.py        # 可视化（画框、标签）
    └── file_utils.py       # 文件路径管理
```

---

## 4. 常用命令

```bash
# 启动 Gradio 控制台
python -m app.main

# 构建 RAG 索引
python -c "from app.rag.rag_tool import build_index; print(build_index())"

# 测试 RAG 查询
python -c "from app.rag.rag_tool import rag_query; print(rag_query('检测到烟雾后应该怎么处理？'))"

# 导出 ONNX 模型
python scripts/export_onnx.py

# 性能基准测试
python scripts/benchmark.py
```

---

## 5. 配置

- 环境变量：`.env`（DEEPSEEK_API_KEY / DEEPSEEK_BASE_URL / DEEPSEEK_MODEL）
- YOLO 模型路径：`app/tools/yolo26n.pt`
- 日志路径：`data/logs/event_log.csv`
- 报告路径：`data/reports/`
- 报警截图：`data/alarms/fire/`
