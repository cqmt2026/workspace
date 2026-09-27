import subprocess
result = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams", r"C:\Users\Administrator\.openclaw\workspace\workspace-pv\data\output\douyin_videos_v2\PV_20260820_171741.mp4"], capture_output=True, text=True)
print(result.stdout[:500])
print(result.stderr[:200])
