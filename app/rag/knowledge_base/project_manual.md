# RoboVision-Agent 项目手册

## 项目定位

RoboVision-Agent 是工业安全场景的本地多工具 AI Agent 控制台。它把视觉检测、RAG 引用问答、事件日志、规则化处置和 SQLite 工单组织为一条可观察的演示链路。

## Agent 工具

| 工具 | 真实实现 | 说明 |
| --- | --- | --- |
| `detect` | YOLO-World / 专项 YOLO | 通用、火焰烟雾、PPE 图片与视频检测。 |
| `detect_open` | YOLO-World `set_classes()` | 开放词汇图片检测；在 UI 中选择“开放词汇检测（图片）”，文本框填写如 `forklift, helmet`。 |
| `rag` | BGE + Chroma | 返回知识库来源文件和 chunk id；LLM 仅为可选生成增强。 |
| `event_log` / `fire_log` | CSV 查询 | 查询留痕与火灾告警历史。 |
| `inspection_report` | 事件日志报告 | 根据已记录事件生成巡检报告。 |
| `disposal` | 规则化工作流 + SQLite | 校验、法规匹配、派单、总结与可选企业微信通知。 |

## 推荐演示顺序

1. 上传图片，选择“火灾烟雾预警”或“开放词汇检测（图片）”。
2. 查看检测摘要、标注结果和 Agent trace；视频输入会返回 H.264 标注视频。
3. 在 RAG 页面查询对应安全规范，核对来源文件和 chunk id。
4. 在事件处置页面使用示例告警，查看 SQLite 工单状态从 `dispatched` 更新为 `completed`。

## 目录与产物

- `app/agent.py`：确定性路由、工具注册和检测后 RAG 复合链。
- `app/runtime/unified_pipeline.py`：YOLO 推理、火灾连续帧规则和视频标注。
- `app/agents/`：规则化处置、企业微信适配器和 SQLite repository。
- `app/rag/`：知识切分、索引和引用检索。
- `data/`：运行时日志、数据库和输出，默认不提交到 Git。

## 边界

本项目不实现多自主 Agent、SAM、模型训练、ONNX/TensorRT 导出、异步队列或生产级认证。第三方权重的训练和精度不作为个人成果陈述。
