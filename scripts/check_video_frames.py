import os, sys, cv2
os.chdir(r"C:\Users\rao'wang\Documents\RoboVision-Agent")
sys.path.insert(0, ".")

import glob
desktop_videos = list(glob.glob(r"C:\Users\rao'wang\Desktop\*top_0_3*"))
fire_video = desktop_videos[0]

# Save a few frames to check what the video contains
cap = cv2.VideoCapture(fire_video)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
fps = cap.get(cv2.CAP_PROP_FPS)
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(f"Video: {total_frames} frames, {fps}fps, {w}x{h}")

# Save frames at key positions
import os as _os
out_dir = "data/debug_frames"
_os.makedirs(out_dir, exist_ok=True)

positions = [0, 50, 200, 400, 600, 800, 1000, 1200, 1400, 1600, 1800, 1900]
for pos in positions:
    if pos >= total_frames:
        continue
    cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(f"{out_dir}/frame_{pos:04d}.jpg", frame)
        # Check for red/orange pixels (fire colors)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # Fire colors: orange-red range in HSV
        lower1 = (0, 100, 100)
        upper1 = (25, 255, 255)
        lower2 = (160, 100, 100)
        upper2 = (180, 255, 255)
        mask1 = cv2.inRange(hsv, lower1, upper1)
        mask2 = cv2.inRange(hsv, lower2, upper2)
        fire_pixels = cv2.countNonZero(mask1) + cv2.countNonZero(mask2)
        total_pixels = w * h
        ratio = fire_pixels / total_pixels * 100
        print(f"Frame {pos}: fire-color pixels={fire_pixels} ({ratio:.2f}%)")

cap.release()
print(f"\nFrames saved to {out_dir}/")
