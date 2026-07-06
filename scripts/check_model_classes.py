import os, sys
os.chdir(r"C:\Users\rao'wang\Documents\RoboVision-Agent")
sys.path.insert(0, ".")

from ultralytics import YOLO

# Check YOLO-World model classes
from app.config import YOLO_WORLD_MODEL
model_path = str(YOLO_WORLD_MODEL)
print(f"Loading {model_path}...")
model = YOLO(model_path)
print(f"Model type: {type(model).__name__}")
print(f"Number of classes: {len(model.names)}")
print(f"Classes: {model.names}")
# Check if fire and smoke are in the classes
for name in model.names.values():
    if 'fire' in name.lower() or 'smoke' in name.lower() or 'flame' in name.lower():
        print(f"  FOUND: {name}")
