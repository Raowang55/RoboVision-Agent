# RoboVision-Agent 全面技术分析

> 生成时间：2026-06-15
> 目的：发给 GPT 获取改进建议

---

## 一、项目定位

**工业视觉预警 Agent 控制台**——一个基于 Gradio 的统一 Web 前端，集成：

- YOLO 实时目标检测（真实推理）
- 火灾烟雾多帧确认预警
- 安全帽/反光衣 PPE 巡检
- 统一事件日志 + 巡检报告自动生成
- 基于 DeepSeek API 的 RAG 知识库问答（语义检索 + LLM 生成）
- 多步链式调用：detect → 提取类别 → RAG 查询规范

**核心代码量**：16 个模块共 3821 行 Python。

---

## 二、技术栈

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 语言 | Python | 3.13 | 全部 |
| 前端 | Gradio | 6.18.0 | Web UI（三标签页） |
| 检测 | Ultralytics YOLO | latest (D:/yolo26) | 目标检测 |
| 视觉 | OpenCV | >=4.8 | 图像读写、画框、视频处理 |
| 向量检索 | ChromaDB + sentence-transformers | 0.5+ / 3.0+ | 语义检索 |
| Embedding | BAAI/bge-small-zh-v1.5 | 512维 | 中文语义向量 |
| LLM | DeepSeek API (OpenAI SDK) | v4-flash | RAG 生成回答 |
| 模型下载 | ModelScope | 1.20+ | 国内可访问的模型源 |
| 图像 | Pillow | >=10.0 | 报告图片转 base64 |
| 配置 | python-dotenv | 1.0+ | .env 环境变量 |

---

## 三、目录结构与模块职责

```
RoboVision-Agent/
├── app/
│   ├── main.py              # Gradio 入口 (644行) — 三标签页 UI + 事件绑定
│   ├── agent.py              # Agent 调度 (522行) — 意图路由 + 工具调度 + 链式调用
│   ├── core/
│   │   ├── media_router.py  # 媒体统一调度 (466行) — 图片/视频/摄像头 → pipeline
│   │   └── event_logger.py  # 统一事件日志写入 (75行) — CSV append + 线程安全
│   ├── tools/               # 9个工具模块
│   │   ├── yolo_tool.py     # [真实] YOLO 检测 — 懒加载单例 + 错误兜底
│   │   ├── event_log_tool.py # 日志查询 + 巡检报告生成
│   │   ├── report_tool.py   # HTML 报告生成 — DeepSeek 安全建议 + base64 图片嵌入
│   │   ├── log_tool.py      # 检测日志查询
│   │   ├── fire_log_tool.py # 火灾报警日志查询
│   │   ├── grounding_tool.py # [Mock] 开放词汇检测
│   │   ├── sam_tool.py      # [Mock] 分割
│   │   ├── dataset_tool.py  # [Mock] 数据集分析
│   │   └── deploy_tool.py   # [Mock] 模型部署
│   │   └── yolo26n.pt       # YOLO 模型权重
│   ├── runtime/             # 运行时管道
│   │   ├── fire_video_detector.py  # 火灾视频检测 (276行)
│   │   ├── fire_alarm_rules.py     # 连续帧确认报警规则 (137行)
│   │   ├── ppe_pipeline.py         # PPE 巡检管道 (101行)
│   │   ├── video_detector.py       # 通用视频检测 (237行)
│   │   └── unified_pipeline.py     # 统一检测管道
│   ├── llm/
│   │   └── deepseek_client.py     # DeepSeek API 客户端 (89行) — OpenAI SDK + .env
│   ├── rag/                 # RAG 知识库模块
│   │   ├── rag_tool.py      # RAG 统一入口 (96行) — 检索→Prompt→LLM→兜底
│   │   ├── vector_store.py  # 语义向量检索 (190行) — ChromaDB + BGE
│   │   ├── prompt_builder.py # Prompt 构造 (107行) — 结构化输出要求
│   │   ├── document_loader.py # 文档加载 + 文本切块 (64行)
│   │   ├── knowledge_base/  # 4个 .md 知识库文件
│   │   │   ├── fire_safety.md      # 火灾/烟雾报警分级处置
│   │   │   ├── ppe_rules.md        # 安全帽/反光衣佩戴规范
│   │   │   ├── deployment_guide.md # Jetson/ONNX 部署指南
│   │   │   └── project_manual.md   # 项目功能手册
│   │   ├── chroma_db/       # ChromaDB 持久化（不提交）
│   │   └── models/          # BGE 模型文件（不提交）
│   └──  utils/              # 工具函数
│       ├── file_utils.py
│       ├── image_utils.py
│       └── vis_utils.py
├── scripts/                 # 辅助脚本
│   ├── test_rag.py          # RAG 一键健康检查
│   ├── test_rag_acceptance.py # RAG 5项验收测试
│   ├── train_yolo.py
│   ├── export_onnx.py
│   └── benchmark.py
├── configs/                 # 配置文件
├── data/                    # 运行时数据
│   ├── logs/event_log.csv   # 统一事件日志
│   ├── outputs/             # 检测结果图/视频
│   └── reports/             # 生成的报告
├── .env                     # DeepSeek API Key（不提交）
├── .gitignore
├── requirements.txt
├── README.md
└── PROJECT_STATUS.md        # 项目状态总结（旧版）
```

---

## 四、闭环逻辑（完整数据流）

### 4.1 三种用户入口

```
用户输入
├── 上传图片/视频 + 文本指令 → detect_media() [media_router]
├── 纯文本指令 → run_agent() [agent]
└── RAG 问答标签页 → rag_chat() [main]
```

### 4.2 检测管线（图片/视频）

```
Gradio 上传文件
  → process() [main.py]
    → detect_media() [media_router.py]
      → 判断媒体类型: image / video / camera
      → 判断任务类型: auto → 关键词匹配 fire/ppe/general
      → 解析模型路径: fire_smoke_*.pt → yolo26n.pt 兜底
      →
      ├── [图片] _detect_image()
      │   → YOLO 推理 → 解析结果 → 保存标注图
      │   → append_event() 写入 event_log.csv（每条检测）
      │
      └── [视频] _detect_video_or_camera()
          → OpenCV 逐帧读取 (stride=N)
          → YOLO 推理 → 画框
          → FireAlarmEngine 连续帧确认（仅 fire 任务）
          → 报警时保存截图 + append_event(is_alarm=True)
          → 输出标注视频 + 检测日志 CSV
    → 返回 {summary, output_image, output_video, detections, log_path}
  → Gradio 渲染: Markdown + 标注图 + 视频 + JSON
```

### 4.3 Agent 文本查询管线

```
用户输入文本（无文件）
  → run_agent() [agent.py]
    → parse_intent() 11级优先级关键词匹配:
        chain → detect_open → segment → analyze → report
        → deploy → rag → inspection_report → event_log
        → fire_log → detect(默认)
    →
    ├── [chain] 多步链式: detect 图片 → 提取 class_names → rag_query
    ├── [rag] RAG: rag_query → DeepSeek 生成（含日志上下文）
    ├── [event_log] 日志查询
    ├── [inspection_report] 巡检报告生成
    ├── [detect] YOLO 检测
    └── [...] 其他工具
    → 返回 {intent, result, annotated_image}
  → _format_agent_result() 格式化 Markdown
  → Gradio 渲染
```

### 4.4 RAG 问答管线

```
用户输入问题
  → rag_query() [rag_tool.py]
    → vector_store.search() [ChromaDB]
      → sentence-transformers.encode(question) → 512维向量
      → ChromaDB collection.query() → top-k 相似 chunks
    → prompt_builder.build_rag_prompt()
      → 结构化 Prompt: 角色 → 规则 → 引用来源 → 禁止编造
      → 融合 log_context（如有报警上下文）
    → deepseek_client.chat() [OpenAI SDK]
      → POST https://api.deepseek.com
      → 成功: 返回 LLM 回答
      → 失败: build_fallback_answer() 拼接检索片段
    → 返回 {answer, retrieved_chunks, source_files, used_llm, model}
  → Gradio 渲染: 回答 + 来源 + 检索片段 + 模型信息
```

### 4.5 链式调用管线（检测 + RAG）

```
用户上传图片 + 输入包含"并"/"然后"/"接着"等连接词
  → process() [main.py] Case 0 检测 _is_chain_query()
    → run_agent(image=img, text_prompt)
      → _run_chain():
        1. detect(image) → detections
        2. 提取 class_names → 翻译中文名（如 person→人员）
        3. rag_query(f"检测到 {names}，相关安全规范是什么？")
        4. 合并 answer: 检测摘要 + RAG 回答 + 来源
      → 返回 {answer, detections, rag_answer, used_chain, decision_trace}
  → Gradio 渲染: 检测结果 + RAG Knowledge Base Answer + 决策追踪
```

### 4.6 巡检报告管线

```
用户输入"生成巡检报告"
  → run_agent() → intent=inspection_report
    → generate_inspection_report() [event_log_tool.py]
      → query_event_log() 读取 event_log.csv
      → 统计: total_events, total_alarms, by_task_type, by_class_name,
              by_alarm_level, low_confidence(<0.3), recent_alarms
      → 生成 Markdown 报告 → 保存 data/reports/inspection_report_*.md
    → 返回 {report_markdown, report_path, alarm_images}
  → Gradio 渲染: 报告 Markdown + 报警截图
```

---

## 五、完成度矩阵

| 模块 | 状态 | 行数 | 核心能力 |
|------|------|------|------|
| YOLO 检测 | ✅ 真实 | 187 | 懒加载单例、错误全兜底、标注图保存 |
| 火灾视频检测 | ✅ 真实 | 276 | 逐帧推理、报警截图、OpenCV 画框 |
| 火灾报警规则 | ✅ 真实 | 137 | fire≥0.5×3帧→HIGH, smoke≥0.4×10帧→MEDIUM, 冷却机制 |
| PPE 巡检 | ⚠️ 管道 | 101 | 管道已建，依赖专用模型 |
| 统一事件日志 | ✅ 真实 | 75 | 14字段 CSV、线程安全、自动建表 |
| 事件日志查询 | ✅ 真实 | 293 | 多维度统计、低置信度筛选、报告生成 |
| 巡检报告 | ✅ 真实 | 293 | Markdown 报告、报警截图收集 |
| RAG 知识库 | ✅ 真实 | 457 | 语义检索 + DeepSeek 生成 + 兜底 + 日志融合 |
| DeepSeek LLM | ✅ 真实 | 89 | OpenAI SDK、.env 配置、失败兜底 |
| 意图路由 | ✅ 真实 | 522 | 11级优先级、链式调用、关键词匹配 |
| Gradio 前端 | ✅ 真实 | 644 | 三标签页、自定义 CSS、RAG 独立界面 |
| HTML 报告 | ✅ 真实 | 337 | base64 图片嵌入、DeepSeek 安全建议 |
| 开放词汇检测 | ❌ Mock | - | 待接入 GroundingDINO |
| SAM 分割 | ❌ Mock | - | 待接入 SAM |
| 数据集分析 | ❌ Mock | - | 占位 |
| 模型部署 | ❌ Mock | - | 占位 |
| 实时视频流 | ❌ 未实现 | - | 当前仅离线处理 |

---

## 六、核心设计决策

1. **不使用 LangChain**：RAG 模块用原生 Python + ChromaDB + OpenAI SDK 实现，保持简单可理解。

2. **模型懒加载单例**：`yolo_tool._load_model()` 使用模块级 `_model` 变量缓存，避免重复加载。但进程重启后丢失缓存，启动约需 30s。

3. **语义向量检索**：从最初 TF-IDF 升级到 `BAAI/bge-small-zh-v1.5` (512维) + ChromaDB，支持中英文混合检索。

4. **ModelScope 替代 HuggingFace**：因网络不可达，BGE 模型通过 ModelScope 下载。

5. **统一事件日志**：所有检测和报警事件写入同一个 `event_log.csv`，14 个字段覆盖完整上下文。

6. **LLM 失败自动兜底**：DeepSeek API 调用失败时，自动拼接检索片段作为回答，不中断服务。

7. **知识库诚实原则**：Prompt 要求模型在证据不足时明确说明"无法给出确定回答"，禁止编造。

8. **链式调用**：检测到"并"、"然后"等连接词 + 前半检测关键词 + 后半规范关键词时，自动执行 detect → extract → RAG 三步链。

9. **双日志格式**：`event_log.csv`（统一格式） + `*_YYYYMMDD.csv`（每次运行的独立日志），兼容易读性和程序处理。

10. **纯 stdlib + PIL 报告**：HTML 报告不引入 reportlab/weasyprint，用内联 CSS + base64 图片。

---

## 七、环境配置

```bash
# .env
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash

# 启动
conda activate robovision
python -m app.main
# → http://127.0.0.1:7860
```

---

## 八、已知问题与改进方向

### 高优先级
1. **5个 Mock 模块未接入真实模型**：GroundingDINO、SAM、PPE 专用模型、数据集分析、ONNX/TensorRT 导出
2. **PPE 缺少专用模型**：`ppe_pipeline.py` 管道已搭建但用通用 YOLO 代替
3. **火灾专用模型缺失**：`fire_smoke_yolo26n.pt` 不存在，降级为通用 yolo26n.pt
4. **启动速度**：Gradio 6.x + YOLO + embedding 模型加载约 2-3 分钟
5. **实时视频流**：前端仅支持上传视频后离线处理，不支持 RTSP/摄像头实时流

### 中优先级
6. **意图路由歧义**：纯关键词匹配存在冲突（如"报告"同时命中 inspection_report 和 report）
7. **RAG 前端体验**：回答在 Markdown 框中，无打字机效果/流式输出
8. **错误提示不统一**：部分模块用 f-string，部分用 traceback
9. **模型热加载**：每次进程重启重新加载所有模型

### 低优先级
10. **单元测试缺失**：无 pytest 覆盖
11. **路径硬编码**：`D:/yolo26` 硬编码在 yolo_tool.py 和 media_router.py 中
12. **多语言支持**：知识库和提示词以中文为主，英文有限
13. **日志无大小限制**：event_log.csv 无限增长
14. **CSS 离页面级设计还有差距**：目前是功能性 UI，不够精致

---

## 九、端到端验证结果（2026-06-15）

使用 `15111458_2160_3840_30fps.mp4` (13.3MB) 进行全流程闭环测试：

| 步骤 | 操作 | 耗时 | 结果 |
|------|------|------|------|
| 视频检测 | detect_media(video, stride=30, 5 frames) | 9.2s | 19 detections: person(14), car(3), truck(1) |
| 日志写入 | event_log.csv append | - | 65 events, 14 fields |
| 日志查询 | run_agent("查看日志") | <1s | intent→event_log ✅ |
| 巡检报告 | run_agent("生成巡检报告") | 14s | inspection_report_*.md, 65 events, 0 alarms |
| RAG 问答 | rag_chat("检测到人员后安全措施") | 56s | used_llm=True, model=deepseek-v4-flash, sources 正确 |

**全流程 5 步通过，无报错。** 发现并修复了 event_log.csv 重复表头 bug。

---

## 十、给 GPT 的核心问题

> 请基于以上分析，给出以下方面的改进建议：

1. **架构层面**：当前 Agent 调度是关键词匹配，需要升级到什么程度？（LLM Router？ReAct？Plan-and-Execute？）
2. **RAG 增强**：当前是简单的检索+生成，如何加入 HyDE、reranker、多轮对话记忆？
3. **前端升级**：Gradio 适合原型但不够产品化，推荐什么前端方案？（Streamlit？FastAPI + React？）
4. **性能优化**：启动慢（3分钟）、视频检测帧率低，有哪些优化方案？
5. **模型层**：Mock 模块（GroundingDINO, SAM, PPE）的接入优先级和方案？
6. **工程化**：测试、CI/CD、配置管理、日志轮转等工程实践建议？
7. **产品化路径**：从 Demo 到生产部署，还缺哪些能力？
