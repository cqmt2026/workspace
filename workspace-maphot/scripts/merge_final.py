# -*- coding: utf-8 -*-
import subprocess
import os

BASE = r"C:\Users\Administrator\.openclaw\workspace\workspace-maphot"
VIDEO_IN = os.path.join(BASE, "my-video", "city_广州_fixed.mp4")
AUDIO_IN = os.path.join(BASE, "data", "audio", "city_广州_tts.mp3")
VIDEO_OUT = os.path.join(BASE, "data", "videos", "广州11区GDP排名_完整版.mp4")

print(f"Video: {VIDEO_IN}")
print(f"Audio: {AUDIO_IN}")
print(f"Output: {VIDEO_OUT}")

cmd = [
    "ffmpeg", "-y",
    "-i", VIDEO_IN,
    "-i", AUDIO_IN,
    "-c:v", "copy",
    "-c:a", "aac", "-b:a", "128k",
    "-shortest",
    VIDEO_OUT
]

result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
print(result.stderr[-500:] if result.stderr else "OK")

if os.path.exists(VIDEO_OUT):
    size = os.path.getsize(VIDEO_OUT)
    print(f"Size: {size/1024/1024:.1f}MB")
else:
    print("Output not created")
