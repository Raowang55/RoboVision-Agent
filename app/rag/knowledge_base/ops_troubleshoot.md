# RoboVision-Agent 运维与故障排查

## 快速诊断

```bash
python scripts/doctor.py --json
python -m ruff check app tests scripts run_server.py
python -m pytest tests -m "not model and not llm" -q
```

## 检测与媒体

| 现象 | 处理方式 |
| --- | --- |
| 模型缺失 | 运行 `python scripts/download_models.py`，确认 `weights/yolov8s-worldv2.pt` 和 `weights/fire_smoke_yolov8n.pt` 已存在。 |
| 图片无法读取 | 使用有效的 JPG、PNG、BMP、TIFF 或 WebP 路径；开放词汇检测只接受图片。 |
| 视频没有播放器画面 | 安装项目依赖中的 `imageio-ffmpeg`；处理完成后应返回 H.264 MP4。 |
| 没有火灾告警截图 | 只有模型明确检测到连续的 `fire` 或 `smoke` 并满足冷却规则时才生成告警。`unclassified` 不会被当作火灾。 |

## RAG 与 LLM

| 现象 | 处理方式 |
| --- | --- |
| 首次检索较慢 | Embedding 模型与 Chroma 索引按需初始化；后续检索会复用缓存。 |
| 无法加载 Embedding | 检查网络或在 `EMBEDDING_MODEL_PATH` 指向本地 SentenceTransformer 模型目录。无需安装未声明的 `modelscope`。 |
| 云端回答失败 | 检查 `LLM_BASE_URL`、`LLM_MODEL`、`LLM_API_KEY`；应用会在一次超时后回退到引用检索结果。 |

## 通知与工单

企业微信适配器仅在 `WECHAT_ENABLED=true` 且配置了 `WECHAT_WEBHOOK_KEY` 时发送请求。页面的“已推送”仅在企业微信接口返回 `errcode=0` 时显示；其他状态会给出未启用、HTTP 错误或接口拒绝的原因。
