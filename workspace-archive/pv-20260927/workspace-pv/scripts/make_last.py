import subprocess, os, tempfile, shutil, edge_tts, asyncio
from pathlib import Path

BASE = Path(r"C:\Users\Administrator\.openclaw\workspace\workspace-pv")
tmp = tempfile.mkdtemp(prefix='pv6d_last_')
src = str(BASE / "data" / "materials" / "solar_eclipse_370344.mp4")
dst_out = str(BASE / "data" / "output" / "douyin_videos_v6" / "PV_20260820_171748.mp4")

# 获取素材时长
r = subprocess.run(["ffmpeg", "-i", src], capture_output=True, text=True, timeout=10)
dur = 10.0
for line in r.stderr.split("\n"):
    if "Duration:" in line:
        parts = line.split(",")[0].strip().split("Duration: ")[1]
        h, m, s = parts.split(":")
        dur = int(h)*3600 + int(m)*60 + float(s)
print(f"素材时长: {dur:.1f}s")

# 截取5秒(用很短的片段避免超时)
clipped = os.path.join(tmp, "clipped.mp4")
subprocess.run(["ffmpeg", "-y", "-i", src, "-t", "5", "-c", "copy", clipped], capture_output=True, timeout=10)

# TTS - 短文案
full = "6家巨头拿下4.3GW大单，这波你站谁？中核集采入围的都是头部企业。不懂怎么选组件？私信我城市+屋顶类型。"
audio = os.path.join(tmp, "tts.mp3")
communicate = edge_tts.Communicate(full, "zh-CN-XiaoxiaoNeural")
asyncio.run(communicate.save(audio))
print(f"TTS: {os.path.getsize(audio)} bytes")

# drawtext - 用非常短的滤镜
esc = "6家巨头拿下4.3GW大单"
vf = f"drawtext=text='{esc}':fontsize=28:fontcolor=white:x=(w-text_w)/2:y=h-80"
subbed = os.path.join(tmp, "subbed.mp4")
r2 = subprocess.run(["ffmpeg", "-y", "-i", clipped, "-vf", vf, "-c:v", "libx264", "-preset", "ultrafast", "-crf", "30", "-c:a", "copy", subbed], capture_output=True, timeout=30)
print(f"drawtext: rc={r2.returncode}")
if r2.returncode != 0:
    print(f"err: {r2.stderr.decode('utf-8', errors='replace')[-200:]}")

# 合音频
final = os.path.join(tmp, "final.mp4")
r3 = subprocess.run(["ffmpeg", "-y", "-i", subbed, "-i", audio, "-c:v", "copy", "-c:a", "aac", "-b:a", "96k", "-shortest", final], capture_output=True, timeout=30)
print(f"merge: rc={r3.returncode}")

shutil.copy2(final, dst_out)
r4 = subprocess.run(["ffmpeg", "-i", dst_out], capture_output=True, text=True, timeout=10)
for line in r4.stderr.split("\n"):
    if "Duration:" in line:
        print(f"最终: {line.strip()[:60]} | {os.path.getsize(dst_out)/1024/1024:.1f}MB")
        break

shutil.rmtree(tmp, ignore_errors=True)