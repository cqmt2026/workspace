# -*- coding: utf-8 -*-
"""
为60秒视频添加字幕
"""
import subprocess
import os
import re

# 视频路径
video_path = r"C:\Users\Administrator\.openclaw\workspace\workspace-maphot\data\videos\city_广州_final_60s.mp4"
output_path = r"C:\Users\Administrator\.openclaw\workspace\workspace-maphot\data\videos\city_广州_final_60s_sub.mp4"

# 字幕配置（基于脚本内容）
subtitles = [
    (0, 3, "同一个广州"),
    (3, 6, "一个区顶15个从化"),
    (6, 9, "差距39倍"),
    (9, 14, "天河7017亿"),
    (14, 18, "金融心脏"),
    (18, 23, "黄埔4346亿"),
    (23, 27, "工业脊梁"),
    (27, 32, "越秀3545亿"),
    (32, 35, "小而精"),
    (35, 40, "白云番禺咬得很紧"),
    (40, 45, "海珠增速冠军"),
    (45, 49, "琶洲互联网集聚"),
    (49, 54, "南沙潜力最大"),
    (54, 57, "花都汽车产业"),
    (57, 60, "你的选择是？"),
]

# 生成ASS字幕文件
ass_lines = [
    "[Script Info]",
    "Title: 广州11区GDP排名",
    "ScriptType: v4.00+",
    "PlayResX: 1080",
    "PlayResY: 1920",
    "",
    "[V4+ Styles]",
    "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
    "Style: Default, Microsoft YaHei, 80, &H00FFFFFF, &H00000000, &H00000000, &H00000000, 0, 0, 0, 0, 100, 100, 0, 0, 1, 3, 2, 2, 50, 50, 100, 1",
    "",
    "[Events]",
    "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
]

for start, end, text in subtitles:
    start_time = f"{start // 3600:02d}:{(start % 3600) // 60:02d}:{start % 60:02d}.{(start // 10) % 100:02d}"
    end_time = f"{end // 3600:02d}:{(end % 3600) // 60:02d}:{end % 60:02d}.{(end // 10) % 100:02d}"
    ass_lines.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}")

ass_content = "\n".join(ass_lines)
ass_path = r"C:\Users\Administrator\.openclaw\workspace\workspace-maphot\data\videos\subtitle.ass"

with open(ass_path, "w", encoding="utf-8-sig") as f:
    f.write(ass_content)

print(f"ASS字幕已生成: {ass_path}")

# 使用ffmpeg合成字幕
cmd = [
    r"C:\ffmpeg-bin\ffmpeg.exe", "-y",
    "-i", video_path,
    "-vf", f"ass={ass_path}",
    "-c:v", "libx264", "-crf", "18", "-preset", "medium",
    "-c:a", "copy",
    output_path
]

print("开始合成带字幕的视频...")
result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode == 0:
    size = os.path.getsize(output_path)
    print(f"✅ 完成！输出: {output_path}")
    print(f"📦 文件大小: {size / 1024 / 1024:.1f} MB")
else:
    print(f"❌ 失败: {result.stderr}")
