# -*- coding: utf-8 -*-
import subprocess
import os

BASE = r"C:\Users\Administrator\.openclaw\workspace\workspace-maphot"
VIDEO_IN = os.path.join(BASE, "data", "videos", "广州11区GDP排名_最终成品.mp4")
VIDEO_OUT = os.path.join(BASE, "data", "videos", "广州11区GDP排名_带字幕.mp4")
FONT = r"C:\Windows\Fonts\msyh.ttc"

# 字幕数据 (开始秒, 结束秒, 文本)
subtitles = [
    (0, 5, "同一个广州，天河一个区干出7017亿"),
    (5, 10, "比从化多出15倍"),
    (10, 15, "天河靠金融 黄埔靠工业"),
    (15, 20, "两种赚钱方式，把广州劈成两半"),
    (20, 26, "老城靠稳 新区抢风口"),
    (26, 32, "有的吃老本 有的追风口"),
    (32, 38, "从化450亿 主打生态绿城"),
    (38, 44, "你选拼一把还是躺平？"),
    (44, 50, "评论区投票"),
]

# 构建drawtext滤镜
# 使用select滤镜按时间段切换字幕
filters = []
for i, (start, end, text) in enumerate(subtitles):
    # 转义单引号
    text_esc = text.replace("'", "'\\''")
    filter_str = f"drawtext=text='{text_esc}':fontfile='{FONT}':fontsize=55:fontcolor=white:x=(w-text_w)/2:y=h-250:enable='between(t,{start},{end})'"
    filters.append(filter_str)

vf = ",".join(filters)

print(f"Video: {VIDEO_IN}")
print(f"Output: {VIDEO_OUT}")
print(f"Filters: {len(filters)} subtitle segments")

cmd = [
    "ffmpeg", "-y",
    "-i", VIDEO_IN,
    "-vf", vf,
    "-c:a", "copy",
    VIDEO_OUT
]

print("Running ffmpeg...")
result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')

if result.returncode == 0:
    size = os.path.getsize(VIDEO_OUT)
    print(f"SUCCESS: {size/1024/1024:.1f}MB")
else:
    print(f"FAIL: {result.stderr[-500:]}")
