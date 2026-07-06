# RoboVision-Agent Knowledge Base — YOLO & Agent 部署指南

---

## 1. 本地部署（Windows / Linux）

### 1.1 环境要求

| 项目 | 最低配置 | 推荐配置 |
|------|----------|----------|
| Python | 3.10+ | 3.11+ |
| CUDA | 无（CPU 可用） | 11.8+（GPU 推理） |
| 内存 | >= 8 GB | >= 16 GB |
| 磁盘 | >= 5 GB | >= 10 GB |

### 1.2 安装步骤

```bash
pip install ultralytics opencv-python gradio chromadb sentence-transformers openai python-dotenv
```

### 1.3 模型文件

| 模型 | 默认路径 | 用途 |
|------|----------|------|
| 通用检测 | `app/tools/yolo26n.pt` | COCO 80 类目标检测 |
| 火灾检测 | `weights/fire_smoke_yolo26n.pt` | 火灾烟雾专用（如不存在则回退到通用模型） |

### 1.4 启动命令

```bash
# 启动 Gradio 控制台
python -m app.main

# 浏览器打开 http://127.0.0.1:7861
# 如果端口被占用，自动尝试 7862、7863...
```

---

## 2. Jetson 部署

### 2.1 支持平台

- Jetson Orin / AGX Orin / Xavier NX / Xavier AGX
- JetPack 5.0+

### 2.2 模型导出

```bash
python scripts/export_onnx.py    # 导出 ONNX 格式
python scripts/benchmark.py      # 性能基准测试
```

### 2.3 性能优化

| 优化项 | 说明 |
|--------|------|
| FP16 精度 | 显著降低显存占用，精度损失可忽略 |
| 批量推理 | batch_size >= 4 提升吞吐 |
| 跳帧检测 | frame_stride=5，每 5 帧检测一次 |
| TensorRT | 使用 `scripts/export_onnx.py` 导出后加速 |

---

## 3. 摄像头接入

| 输入类型 | 示例 | 配置位置 |
|----------|------|----------|
| USB 摄像头 | `source=0` | Gradio 前端 "视频源" 输入框 |
| RTSP 流 | `source=rtsp://192.168.1.100:554/stream` | 同上 |
| 本地视频 | `source=D:/video.mp4` | 同上 |
| 图片上传 | 拖拽或点击上传 | Gradio "上传文件" 组件 |

---

## 4. 环境变量配置

在项目根目录 `.env` 文件中：

```ini
DEEPSEEK_API_KEY=sk-xxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
```

---

## 5. 与 RoboVision-Agent 系统联动

- 模型不存在时，系统返回清晰提示，不会崩溃
- CUDA 不可用时，自动回退到 CPU 推理
- 端口被占用时，自动寻找下一个可用端口（7861→7862→...）
- YOLO 模型在后台线程预热，启动后即可使用
