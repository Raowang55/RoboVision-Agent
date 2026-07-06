import os, sys, time, cv2
os.chdir(r"C:\Users\rao'wang\Documents\RoboVision-Agent")
sys.path.insert(0, ".")

import glob
desktop_videos = list(glob.glob(r"C:\Users\rao'wang\Desktop\*top_0_3*"))
fire_video = desktop_videos[0]

# Test with lower confidence
from app.runtime.unified_pipeline import _get_world_model, _set_task_classes

model, is_world = _get_world_model()
print(f"Model loaded, is_world={is_world}")

# Set fire classes
_set_task_classes(model, "fire", is_world)

# Read a few frames and test
cap = cv2.VideoCapture(fire_video)
fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
print(f"Video: {total_frames} frames, {fps} fps")

# Test frames at different positions
test_frames = [0, total_frames//4, total_frames//2, 3*total_frames//4, total_frames-10]
for target_frame in test_frames:
    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
    ret, frame = cap.read()
    if not ret:
        print(f"Frame {target_frame}: read failed")
        continue
    
    # Test with different conf thresholds
    for conf in [0.05, 0.1, 0.15, 0.25]:
        results = model(frame, conf=conf, verbose=False)
        if results[0].boxes is not None:
            names = [results[0].names[int(b.cls[0])] for b in results[0].boxes]
            confs = [round(b.conf[0].item(), 3) for b in results[0].boxes]
            print(f"Frame {target_frame}, conf={conf}: {list(zip(names, confs))}")
        else:
            print(f"Frame {target_frame}, conf={conf}: no detections")
    break  # Just test one frame for now

cap.release()
