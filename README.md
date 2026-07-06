# RoboVision Agent

Multi-tool computer vision agent with a Gradio web UI.

## Features

- **Object Detection** — YOLO-based detection with mock results
- **Open-Vocabulary Detection** — Find objects by natural language (Grounding DINO style)
- **Segmentation** — SAM-based instance segmentation
- **Dataset Analysis** — Synthetic dataset statistics
- **Report Generation** — Visual reports with bounding boxes and masks
- **Model Deployment** — ONNX / TensorRT export placeholders

## Quick Start

```bash
pip install -r requirements.txt
python -m app.main
```

Open [http://127.0.0.1:7860](http://127.0.0.1:7860) in your browser.

## Project Structure

```
RoboVision-Agent/
├── app/
│   ├── main.py              # Gradio web UI entry point
│   ├── agent.py             # Agent scheduler — intent parsing + tool routing
│   ├── tools/
│   │   ├── yolo_tool.py      # YOLO detection (mock)
│   │   ├── grounding_tool.py # Open-vocabulary detection (mock)
│   │   ├── sam_tool.py       # SAM segmentation (mock)
│   │   ├── dataset_tool.py   # Dataset analysis (mock)
│   │   ├── report_tool.py    # Report generation (mock)
│   │   └── deploy_tool.py    # ONNX/TensorRT deployment (mock)
│   └── utils/
│       ├── image_utils.py    # Load / resize / save images
│       ├── vis_utils.py      # Draw boxes, masks, labels
│       └── file_utils.py     # File-system helpers
├── configs/
│   ├── model_config.yaml     # Model settings
│   └── agent_config.yaml     # Agent & UI settings
├── data/
│   ├── images/               # Drop input images here
│   ├── outputs/              # Processed outputs
│   └── reports/              # Generated reports
├── scripts/
│   ├── train_yolo.py         # Training placeholder
│   ├── export_onnx.py        # ONNX export placeholder
│   └── benchmark.py          # Inference benchmark placeholder
├── requirements.txt
└── README.md
```

## Usage

1. Upload an image via the Gradio UI.
2. Type an instruction, e.g.:
   - `detect objects` — runs YOLO mock detection
   - `find all cars and people` — open-vocabulary detection
   - `segment the main object` — runs SAM mock segmentation
   - `generate report` — creates a visual report
   - `analyze dataset` — shows synthetic dataset stats
   - `deploy yolo to onnx` — mock model export
3. Click **Run** to see the results and annotated image.

## Replacing Mocks with Real Models

Each tool under `app/tools/` wraps a single function. To swap in real models:

- `yolo_tool.py` → replace with `ultralytics.YOLO`
- `grounding_tool.py` → replace with Grounding DINO / OWL-ViT
- `sam_tool.py` → replace with `segment_anything.SamPredictor`
- `dataset_tool.py` → replace with real dataset parsing (COCO, YOLO, VOC)
- `deploy_tool.py` → wire up `torch.onnx.export` / TensorRT builder
