import subprocess, os
from pathlib import Path

BASE = Path(r"C:\Users\Administrator\.openclaw\workspace\workspace-pv\data\output\douyin_videos_v5")
for f in sorted(BASE.glob("*.mp4"), key=lambda x: x.stat().st_size, reverse=True):
    if "TEST" in f.name: continue
    # 获取视频时长
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", str(f)],
                       capture_output=True, text=True, timeout=5)
    dur = float(r.stdout.strip()) if r.stdout.strip() else 0
    print(f"{f.name}: {dur:.1f}s | {os.path.getsize(f)/1024/1024:.1f}MB")