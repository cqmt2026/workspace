# -*- coding: utf-8 -*-
import subprocess
import os

BASE = r"C:\Users\Administrator\.openclaw\workspace\workspace-maphot"
VIDEO_IN = os.path.join(BASE, "data", "videos", "广州11区GDP排名_流水线版.mp4")
VIDEO_OUT = os.path.join(BASE, "data", "videos", "广州11区GDP排名_最终成品.mp4")
AUDIO_BGM = os.path.join(BASE, "data", "audio", "bgm_funk.mp3")

# 步骤1: 直接混合BGM（不过滤字幕，先保证有声音）
print("Step 1: Mix BGM...")
cmd = [
    "ffmpeg", "-y",
    "-i", VIDEO_IN,
    "-i", AUDIO_BGM,
    "-filter_complex", "[1:a]volume=0.1[a];[0:a][a]amix=inputs=2:duration=first",
    "-c:v", "copy",
    "-c:a", "aac", "-b:a", "128k",
    VIDEO_OUT
]

result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
if result.returncode == 0:
    size = os.path.getsize(VIDEO_OUT)
    print(f"OK: {VIDEO_OUT} ({size/1024/1024:.1f}MB)")
else:
    print(f"FAIL: {result.stderr[-300:]}")
