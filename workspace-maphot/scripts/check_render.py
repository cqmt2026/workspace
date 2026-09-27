#!/usr/bin/env python3
"""检查渲染视频和音频配置"""
import os, re, subprocess

root = r"C:\Users\Administrator\.openclaw\workspace\workspace-maphot\my-video"
html = open(os.path.join(root, "index.html"), encoding="utf-8").read()

# Find audio references
audio_refs = re.findall(r'src=["\x27]([^"\x27]*audio[^"\x27]*)["\x27]', html, re.IGNORECASE)
print("Audio src refs:", audio_refs)

# Find audio tags
audio_tags = re.findall(r'<audio[^>]*>.*?</audio>', html, re.DOTALL)
print(f"Audio tags found: {len(audio_tags)}")
for t in audio_tags[:3]:
    print(t[:200])

# Check if assets/audio.mp3 exists
audio_path = os.path.join(root, "assets", "audio.mp3")
print(f"\naudio.mp3 exists: {os.path.exists(audio_path)}")
if os.path.exists(audio_path):
    print(f"  size: {os.path.getsize(audio_path)} bytes")

# Check video file
video_path = os.path.join(root, "city_广州_final.mp4")
print(f"\nVideo file exists: {os.path.exists(video_path)}")
if os.path.exists(video_path):
    print(f"  size: {os.path.getsize(video_path)} bytes ({os.path.getsize(video_path)/1024/1024:.2f} MB)")

# Try ffprobe
try:
    result = subprocess.run([
        r"C:\ffmpeg-bin\ffprobe.exe", "-v", "quiet", "-show_format", "-show_streams",
        video_path
    ], capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(f"\nffprobe output:\n{result.stdout[:1500]}")
    if result.stderr:
        print(f"ffprobe stderr:\n{result.stderr[:500]}")
except Exception as e:
    print(f"ffprobe error: {e}")
