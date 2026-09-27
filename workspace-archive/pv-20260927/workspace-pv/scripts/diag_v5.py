# -*- coding: utf-8 -*-
"""视频时长诊断 - 找出截断根因"""
import subprocess, os, json
from pathlib import Path

BASE = Path(r"C:\Users\Administrator\.openclaw\workspace\workspace-pv")

# 1. 检查V5视频是否有效
videos = list((BASE / "data" / "output" / "douyin_videos_v5").glob("*.mp4"))
print("=== V5 视频检查 ===")
for v in videos:
    if "TEST" in v.name: continue
    size = os.path.getsize(v)
    # 用ffmpeg读取视频流信息
    r = subprocess.run(["ffmpeg", "-i", str(v)], capture_output=True, text=True, timeout=10)
    # 找Duration和Video/Audio行
    lines = r.stderr.split("\n")
    dur_line = [l for l in lines if "Duration:" in l]
    video_line = [l for l in lines if "Stream #0:0" in l]
    audio_line = [l for l in lines if "Stream #0:1" in l]
    dur = dur_line[0].strip() if dur_line else "N/A"
    has_video = len(video_line) > 0
    has_audio = len(audio_line) > 0
    print(f"  {v.name}: {size/1024/1024:.1f}MB | {dur} | video={has_video} audio={has_audio}")

# 2. 检查素材长度
mat = BASE / "data" / "materials"
print("\n=== 素材长度 ===")
for m in sorted(mat.glob("*.mp4"), key=lambda x: -x.stat().st_size)[:10]:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", str(m)],
                       capture_output=True, text=True, timeout=5)
    dur = float(r.stdout.strip()) if r.stdout.strip() else 0
    print(f"  {m.name}: {dur:.1f}s | {m.stat().st_size/1024/1024:.1f}MB")

# 3. 检查文案需要多长
print("\n=== 文案时长估算 ===")
jf = BASE / "data" / "output" / "llm_generated" / "llm_generated_20260820.json"
with open(jf, "r", encoding="utf-8") as f:
    contents = json.load(f)
for i, c in enumerate(contents[:10]):
    body = c.get("body", "")
    hook = c.get("hook", "")
    cta = c.get("cta", "")
    chars = len(hook + body + cta)
    est_dur = chars / 5
    print(f"  [{i+1}] {c['direction']:8s} | {chars:4d}字 | 需{est_dur:.0f}s | 素材仅10s -> 严重不足")