import subprocess, os
videos = [
    r"C:\Users\Administrator\.openclaw\workspace\workspace-pv\data\output\douyin_videos_v5\PV_20260820_171741.mp4",
    r"C:\Users\Administrator\.openclaw\workspace\workspace-pv\data\output\douyin_videos_v5\PV_20260820_171812.mp4",
    r"C:\Users\Administrator\.openclaw\workspace\workspace-pv\data\output\douyin_videos_v5\PV_20260820_172003.mp4",
]
for v in videos:
    print(f"\n=== {os.path.basename(v)} ({os.path.getsize(v)/1024/1024:.1f}MB) ===")
    r = subprocess.run(["ffprobe", "-v", "error", "-show_streams", v], capture_output=True, text=True, timeout=10)
    for line in r.stdout.split("\n"):
        stripped = line.strip()
        if any(k in stripped for k in ["codec_name=", "width=", "height=", "duration=", "nb_frames=", "codec_type="]):
            print(f"  {stripped}")
    has_sub = "Subtitle" in r.stdout or "subrip" in r.stdout.lower()
    print(f"  -> {'有软字幕流' if has_sub else '无软字幕流（字幕应已烧录进视频）'}")
