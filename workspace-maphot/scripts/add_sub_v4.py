# -*- coding: utf-8 -*-
import subprocess
import os

BASE = r"C:\Users\Administrator\.openclaw\workspace\workspace-maphot"
VIDEO_IN = os.path.join(BASE, "data", "videos", "广州11区GDP排名_最终成品.mp4")
VIDEO_OUT = os.path.join(BASE, "data", "videos", "广州11区GDP排名_字幕版.mp4")
ASS_FILE = "subs_new.ass"

# 创建新的ASS文件
ass_content = """[Script Info]
Title: 广州11区GDP排名
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Microsoft YaHei,60,&H00FFFFFF,&H00000000,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,3,2,2,50,50,150,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,00:00:00.00,00:00:05.00,Default,,0,0,0,,同一个广州，天河一个区干出7017亿
Dialogue: 0,00:00:05.00,00:00:10.00,Default,,0,0,0,,比从化多出15倍
Dialogue: 0,00:00:10.00,00:00:15.00,Default,,0,0,0,,天河靠金融 黄埔靠工业
Dialogue: 0,00:00:15.00,00:00:20.00,Default,,0,0,0,,两种赚钱方式，把广州劈成两半
Dialogue: 0,00:00:20.00,00:00:26.00,Default,,0,0,0,,老城靠稳 新区抢风口
Dialogue: 0,00:00:26.00,00:00:32.00,Default,,0,0,0,,有的吃老本 有的追风口
Dialogue: 0,00:00:32.00,00:00:38.00,Default,,0,0,0,,从化450亿 主打生态绿城
Dialogue: 0,00:00:38.00,00:00:44.00,Default,,0,0,0,,你选拼一把还是躺平？
Dialogue: 0,00:00:44.00,00:00:50.00,Default,,0,0,0,,评论区投票
"""

# 写入新ASS文件
ass_path = os.path.join(os.path.dirname(VIDEO_IN), ASS_FILE)
with open(ass_path, "w", encoding="utf-8-sig") as f:
    f.write(ass_content)
print(f"Created: {ass_path}")

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
