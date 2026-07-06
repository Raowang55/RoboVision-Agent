import os, sys, cv2
os.chdir(r"C:\Users\rao'wang\Documents\RoboVision-Agent")
sys.path.insert(0, ".")

import glob
desktop_videos = list(glob.glob(r"C:\Users\rao'wang\Desktop\*top_0_3*"))
fire_video = desktop_videos[0]

from app.runtime.unified_pipeline import _get_world_model

model, is_world = _get_world_model()

# Try different text prompts for YOLO-World
prompts_to_try = [
    ["fire", "smoke"],
    ["flame", "smoke"],
    ["fire flame", "smoke cloud"],
    ["burning fire", "smoke"],
    ["fire", "smoke", "explosion"],
    ["orange flame", "black smoke"],
    ["fire", "smoke", "person"],
]

cap = cv2.VideoCapture(fire_video)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

# Test frame 0 which has 32% fire-color pixels
cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
ret, frame = cap.read()

for prompt in prompts_to_try:
    model.set_classes(prompt)
    results = model(frame, conf=0.05, verbose=False)
    if results[0].boxes is not None:
        names = [results[0].names[int(b.cls[0])] for b in results[0].boxes]
        confs = [round(b.conf[0].item(), 3) for b in results[0].boxes]
        print(f"Prompt {prompt}: {list(zip(names, confs))}")
    else:
        print(f"Prompt {prompt}: no detections")

cap.release()
