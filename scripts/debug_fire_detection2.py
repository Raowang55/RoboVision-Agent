import os, sys, cv2
os.chdir(r"C:\Users\rao'wang\Documents\RoboVision-Agent")
sys.path.insert(0, ".")

import glob
desktop_videos = list(glob.glob(r"C:\Users\rao'wang\Desktop\*top_0_3*"))
fire_video = desktop_videos[0]

from app.runtime.unified_pipeline import _get_world_model

model, is_world = _get_world_model()
print(f"Model loaded, is_world={is_world}")

# Check if model supports fire/smoke
if is_world:
    # Test with general classes
    general_classes = ["fire", "smoke", "person", "car", "truck"]
    model.set_classes(general_classes)
    print(f"Set classes: {general_classes}")
    
    cap = cv2.VideoCapture(fire_video)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Test multiple frames
    test_positions = [0, 100, 500, 1000, 1500, 1800]
    for pos in test_positions:
        if pos >= total_frames:
            continue
        cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
        ret, frame = cap.read()
        if not ret:
            continue
        
        results = model(frame, conf=0.1, verbose=False)
        if results[0].boxes is not None:
            names = [results[0].names[int(b.cls[0])] for b in results[0].boxes]
            confs = [round(b.conf[0].item(), 3) for b in results[0].boxes]
            print(f"Frame {pos}: {list(zip(names, confs))}")
        else:
            print(f"Frame {pos}: no detections")
    
    cap.release()
    
    # Also test with the model's default vocabulary
    print("\n--- Testing with default classes ---")
    # Reload model to reset classes
    from app.runtime.unified_pipeline import _WORLD_MODEL
    _WORLD_MODEL = None
    model2, is_world2 = _get_world_model()
    
    cap = cv2.VideoCapture(fire_video)
    for pos in [0, 500, 1000, 1500]:
        cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
        ret, frame = cap.read()
        if not ret:
            continue
        results = model2(frame, conf=0.15, verbose=False)
        if results[0].boxes is not None:
            names = [results[0].names[int(b.cls[0])] for b in results[0].boxes]
            confs = [round(b.conf[0].item(), 3) for b in results[0].boxes]
            print(f"Frame {pos} (default): {list(zip(names, confs))}")
        else:
            print(f"Frame {pos} (default): no detections")
    cap.release()
