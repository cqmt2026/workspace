# -*- coding: utf-8 -*-
import subprocess
import os

BASE = r"C:\Users\Administrator\.openclaw\workspace\workspace-maphot"
VIDEO_IN = os.path.join(BASE, "data", "videos", "广州11区GDP排名_最终成品.mp4")
VIDEO_OUT = os.path.join(BASE, "data", "videos", "广州11区GDP排名_完整版.mp4")
ASS_FILE = "subs.ass"

# 把ASS文件复制到视频同目录，避免路径问题
import shutil
ass_src = os.path.join(BASE, "data", "videos", "subs.ass")
ass_dst = os.path.join(os.path.dirname(VIDEO_IN), ASS_FILE)
shutil.copy2(ass_src, ass_dst)
print(f"Copied ASS to: {ass_dst}")

# 使用相对路径
cmd = [
    "ffmpeg", "-y",
    "-i", VIDEO_IN,
    "-vf", f"ass={ASS_FILE}",
    "-c:v", "libx264", "-crf", "18", "-preset", "fast",
    "-c:a", "copy",
    VIDEO_OUT
]

print("Running...")
result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', cwd=os.path.dirname(VIDEO_IN))

if result.returncode == 0:
    size = os.path.getsize(VIDEO_OUT)
    print(f"\nSUCCESS!")
    print(f"Output: {VIDEO_OUT}")
    print(f"Size: {size/1024/1024:.1f}MB")
else:
    print(f"\nFAIL: {result.stderr[-500:]}")
