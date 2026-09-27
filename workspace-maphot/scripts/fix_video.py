# -*- coding: utf-8 -*-
"""
视频问题修复脚本
1. 添加字幕
2. 混合BGM
3. 输出最终成品
"""
import subprocess
import os

# 路径配置
BASE = r"C:\Users\Administrator\.openclaw\workspace\workspace-maphot"
VIDEO_IN = os.path.join(BASE, "data", "videos", "广州11区GDP排名_流水线版.mp4")
VIDEO_OUT = os.path.join(BASE, "data", "videos", "广州11区GDP排名_最终成品.mp4")
AUDIO_TTS = os.path.join(BASE, "data", "audio", "city_广州_tts.mp3")
AUDIO_BGM = os.path.join(BASE, "data", "audio", "bgm_funk.mp3")
FONT = r"C:\Windows\Fonts\msyh.ttc"

# 字幕数据 (开始秒, 结束秒, 文本)
subtitles = [
    (0, 3, "同一个广州"),
    (3, 6, "天河一个区干出7017亿"),
    (6, 9, "比从化多出15倍"),
    (9, 14, "天河靠金融 黄埔靠工业"),
    (14, 18, "两种赚钱方式"),
    (18, 23, "老城靠稳 新区抢风口"),
    (23, 28, "有的吃老本 有的追风口"),
    (28, 33, "从化450亿 空气最好"),
    (33, 38, "你选拼一把还是躺平？"),
    (38, 45, "评论区投票"),
    (45, 50, "选城市就是选活法"),
]

def run_cmd(cmd):
    """运行命令并返回结果"""
    print(f"执行: {cmd[:80]}...")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    if result.returncode != 0:
        print(f"错误: {result.stderr[-200:]}")
    return result

# 步骤1: 生成带字幕的视频
print("=" * 50)
print("步骤1: 添加字幕")
print("=" * 50)

# 构建drawtext滤镜（使用Pillow生成字幕图片）
# 这里使用ass字幕文件方式
ass_content = """[Script Info]
Title: 广州11区GDP排名
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default, Microsoft YaHei, 70, &H00FFFFFF, &H00000000, &H00000000, &H00000000, 0, 0, 0, 0, 100, 100, 0, 0, 1, 3, 2, 2, 50, 50, 120, 1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

for start, end, text in subtitles:
    start_h = start // 3600
    start_m = (start % 3600) // 60
    start_s = start % 60
    end_h = end // 3600
    end_m = (end % 3600) // 60
    end_s = end % 60
    ass_content += f"Dialogue: 0,{start_h:02d}:{start_m:02d}:{start_s:02d}.00,{end_h:02d}:{end_m:02d}:{end_s:02d}.00,Default,,0,0,0,,{text}\n"

ass_path = os.path.join(BASE, "data", "videos", "subtitle.ass")
with open(ass_path, "w", encoding="utf-8-sig") as f:
    f.write(ass_content)

print(f"ASS字幕已生成: {ass_path}")

# 使用ffmpeg合成字幕
cmd_sub = [
    "ffmpeg", "-y",
    "-i", VIDEO_IN,
    "-vf", f"ass='{ass_path}'",
    "-c:v", "libx264", "-crf", "18", "-preset", "fast",
    "-c:a", "copy",
    os.path.join(BASE, "data", "videos", "video_with_sub.mp4")
]
run_cmd(cmd_sub)

# 步骤2: 混合BGM
print("\n" + "=" * 50)
print("步骤2: 混合BGM")
print("=" * 50)

video_with_sub = os.path.join(BASE, "data", "videos", "video_with_sub.mp4")
video_bgm = os.path.join(BASE, "data", "videos", "video_with_bgm.mp4")

# BGM音量-20dB，淡入淡出2s
cmd_bgm = [
    "ffmpeg", "-y",
    "-i", video_with_sub,
    "-i", AUDIO_BGM,
    "-filter_complex", "[1:a]volume=0.1,afade=din=2:dur=2:start=0,afade=dout=2:start=-2[audio];[0:a][audio]amix=inputs=2:duration=first:dropout_transition=2",
    "-c:v", "copy",
    "-c:a", "aac", "-b:a", "128k",
    video_bgm
]
run_cmd(cmd_bgm)

# 步骤3: 最终输出
print("\n" + "=" * 50)
print("步骤3: 输出最终成品")
print("=" * 50)

if os.path.exists(video_bgm):
    # 复制到最终位置
    import shutil
    shutil.copy2(video_bgm, VIDEO_OUT)
    size = os.path.getsize(VIDEO_OUT)
    print(f"\n✅ 完成！")
    print(f"📦 输出: {VIDEO_OUT}")
    print(f"📊 大小: {size / 1024 / 1024:.1f} MB")
else:
    print("\n❌ 失败")
