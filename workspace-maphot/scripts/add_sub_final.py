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

# 用Python生成ASS文件（UTF-8 with BOM）
ass_lines = [
    "[Script Info]",
    "Title: 广州11区GDP排名",
    "ScriptType: v4.00+",
    "PlayResX: 1080",
    "PlayResY: 1920",
    "",
    "[V4+ Styles]",
    "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
    "Style: Default,Microsoft YaHei,60,&H00FFFFFF,&H00000000,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,3,2,2,50,50,150,1",
    "",
    "[Events]",
    "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
]

for start, end, text in subtitles:
    # 转换为ASS时间格式 (H:MM:SS.CS)
    start_cs = int(start * 100)
    end_cs = int(end * 100)
    start_h = start_cs // 360000
    start_m = (start_cs % 360000) // 6000
    start_s = (start_cs % 6000) // 100
    end_h = end_cs // 360000
    end_m = (end_cs % 360000) // 6000
    end_s = (end_cs % 6000) // 100
    ass_lines.append(f"Dialogue: 0,{start_h:02d}:{start_m:02d}:{start_s:02d}.00,{end_h:02d}:{end_m:02d}:{end_s:02d}.00,Default,,0,0,0,,{text}")

ass_path = os.path.join(BASE, "data", "videos", "subs.ass")
with open(ass_path, "w", encoding="utf-8-sig") as f:
    f.write("\n".join(ass_lines))

print(f"ASS file created: {ass_path}")

# 使用ffmpeg合成
cmd = [
    "ffmpeg", "-y",
    "-i", VIDEO_IN,
    "-vf", f"ass='{ass_path}'",
    "-c:v", "libx264", "-crf", "18", "-preset", "fast",
    "-c:a", "copy",
    VIDEO_OUT
]

print("Rendering with subtitles...")
result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')

if result.returncode == 0:
    size = os.path.getsize(VIDEO_OUT)
    print(f"SUCCESS: {VIDEO_OUT} ({size/1024/1024:.1f}MB)")
else:
    print(f"FAIL: {result.stderr[-500:]}")
