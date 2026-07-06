# RoboVision-Agent Knowledge Base — 运维与故障排查

---

## 1. YOLO 模型相关

### 1.1 模型加载失败

| 现象 | 原因 | 解决方案 |
|------|------|----------|
| 启动时显示 "YOLO load failed" | 模型文件不存在 | 确认 `app/tools/yolo26n.pt` 存在；或从 Ultralytics 下载 |
| 检测时返回 "No image provided" | 未上传图片/视频 | 在 Gradio 前端上传文件或输入视频源地址 |
| 检测结果为空 | 置信度阈值过高 | 在 "高级参数" 中将 conf 降至 0.15 |

### 1.2 GPU 推理问题

| 现象 | 原因 | 解决方案 |
|------|------|----------|
| CUDA out of memory | 显存不足 | 减少 max_frames；使用更小的模型（yolo26n → yolo26n） |
| CUDA 不可用 | 驱动/CUDA 未安装 | 系统自动回退到 CPU 推理，无需手动干预 |

---

## 2. RAG 知识库相关

### 2.1 索引构建失败

| 现象 | 原因 | 解决方案 |
|------|------|----------|
| `ModuleNotFoundError: No module named 'modelscope'` | modelscope 未安装 | `pip install modelscope` |
| Embedding 模型加载失败 | 本地模型不存在且 HuggingFace 下载失败 | 手动下载：`python -c "from modelscope import snapshot_download; snapshot_download('BAAI/bge-small-zh-v1.5', cache_dir='app/rag/models')"` |
| 检索结果为空 | 未构建索引 | 运行 `python -c "from app.rag.rag_tool import build_index; print(build_index())"` |
| 检索结果重复 | 多次构建索引导致重复 | 已内置自动清空旧 collection 逻辑 |

### 2.2 DeepSeek API 调用失败

| 现象 | 原因 | 解决方案 |
|------|------|----------|
| "DEEPSEEK_API_KEY is not set" | `.env` 文件缺少 API Key | 在项目根目录 `.env` 中添加 `DEEPSEEK_API_KEY=sk-xxx` |
| "Request timed out after 20 seconds" | API 响应超时 | 简化问题或检查网络；RAG 已内置 20 秒超时保护 |
| 回答为空或无关 | 知识库缺少相关内容 | 补充 `knowledge_base/` 下的 Markdown 文档后重建索引 |

---

## 3. 摄像头与视频源

| 现象 | 原因 | 解决方案 |
|------|------|----------|
| 摄像头无法打开 | 摄像头编号错误或被占用 | 尝试 source=0 或 source=1；检查其他程序是否占用 |
| RTSP 流连接失败 | 地址错误或网络不通 | 用 VLC 验证 RTSP 地址是否可用 |
| 视频处理卡顿 | 帧率过高或分辨率过大 | 增大 frame_stride（如 5→10）；降低 max_frames |
| 按 q 无法退出 | 视频窗口未获得焦点 | 点击视频窗口后再按 q |

---

## 4. 日志与报告

| 现象 | 原因 | 解决方案 |
|------|------|----------|
| "Event log not found" | 尚未运行过检测 | 先上传图片/视频执行一次检测，日志会自动创建 |
| 报告生成为空 | 日志中没有报警记录 | 确认检测任务产生了报警事件（is_alarm=True） |
| CSV 文件乱码 | 编码问题 | 使用 UTF-8 编码打开；系统内部已使用 UTF-8 |

---

## 5. Gradio 前端与语言切换

| 现象 | 原因 | 解决方案 |
|------|------|----------|
| 页面打不开 (127.0.0.1:7861) | 端口被占用 | 系统自动尝试 7862、7863...；查看终端输出的实际端口 |
| 中文字体显示异常 | 系统缺少中文字体 | 安装 "Microsoft YaHei" 或 "Noto Sans SC" 字体 |
| 切换语言后部分文字未更新 | Gradio 限制 | 标签页名称固定为 mix 模式（中英双语），无法动态切换 |
| "cannot schedule new futures after interpreter shutdown" | 退出时 ChromaDB 线程未清理 | 已修复：atexit 钩子自动清理 ChromaDB 客户端 |

---

## 6. 快速健康检查

```bash
# 检查 RAG 模块是否正常
python scripts/test_rag.py

# 检查模型文件是否存在
ls app/tools/yolo26n.pt

# 检查端口占用
netstat -ano | findstr :7861

# 检查 Gradio 版本
python -c "import gradio; print(gradio.__version__)"
```
