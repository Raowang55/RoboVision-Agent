# RoboVision-Agent 部署指南

## 本地启动

项目使用 Python 3.11 验证。创建虚拟环境后安装项目声明的依赖：

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -e ".[test]"

python scripts/download_models.py
python scripts/doctor.py
python run_server.py
```

控制台默认监听 `127.0.0.1:7861`；端口被占用时会选择后续可用端口。检测模型和索引均按需加载，首次推理可能比后续请求慢。

## 模型文件

模型二进制不提交到 Git。`scripts/download_models.py` 会下载演示需要的通用 YOLO-World 小模型和火焰/烟雾模型，并校验已知文件的 SHA-256。

| 功能 | 默认路径 | 说明 |
| --- | --- | --- |
| 通用与开放词汇检测 | `weights/yolov8s-worldv2.pt` | YOLO-World；开放词汇任务仅支持图片输入，类别由文本框中用逗号分隔的词提供。 |
| 火焰/烟雾检测 | `weights/fire_smoke_yolov8n.pt` | 第三方 YOLOv8n 权重，输出 `fire`、`smoke`。 |
| PPE 检测 | `weights/ppe_v8.pt` | 可选本地权重；缺失时使用通用模型，但不会伪造违规结果。 |
| RAG Embedding | `BAAI/bge-small-zh-v1.5` | 本地缓存优先；没有缓存时由 SentenceTransformers 按其默认机制下载。 |

权重来源、校验值和能力边界见 `weights/README.md`。本项目只集成第三方模型，不主张训练或精度归属。

## 常见问题

- **模型缺失**：运行 `python scripts/download_models.py`，再用 `python scripts/doctor.py --json` 查看状态。
- **浏览器没有视频结果**：项目会使用 `imageio-ffmpeg` 将 OpenCV 输出转为 H.264 MP4；确认依赖已按 `pyproject.toml` 安装。
- **LLM 不可用**：将 `.env.example` 复制为 `.env`，按需设置 `LLM_ENABLED=true`。规则路由、检测、检索和工单不依赖 LLM。
- **企业微信未发送**：设置 `WECHAT_ENABLED=true` 和 `WECHAT_WEBHOOK_KEY`，重启服务；处置页会显示接口确认、未启用或失败原因。

## 范围边界

Jetson、ONNX/TensorRT、训练与生产级用户权限均不在当前仓库的实现范围内。请勿把本项目描述为具备这些能力。
