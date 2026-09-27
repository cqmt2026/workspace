# -*- coding: utf-8 -*-
import subprocess
import os

# 视频路径
video_in = r"C:\Users\Administrator\.openclaw\workspace\workspace-maphot\data\videos\city_广州_final_60s.mp4"
video_out = r"C:\Users\Administrator\.openclaw\workspace\workspace-maphot\data\videos\city_广州_final_60s_sub.mp4"
font = r"C:\Windows\Fonts\msyh.ttc"

# 字幕数据 (开始秒, 结束秒, 文本)
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

# 构建drawtext滤镜
drawtext_filters = []
for start, end, text in subtitles:
    # 转义单引号
    text_escaped = text.replace("'", "'\\''")
    filter_str = f"drawtext=text='{text_escaped}':fontfile='{font}':fontsize=60:fontcolor=white:x=(w-text_w)/2:y=h-200:enable='between(t,{start},{end})'"
    drawtext_filters.append(filter_str)

vf = ",".join(drawtext_filters)

cmd = [
    "ffmpeg", "-y",
    "-i", video_in,
    "-vf", vf,
    "-c:a", "copy",
    video_out
]

print("开始渲染带字幕的视频...")
result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')

if result.returncode == 0:
    size = os.path.getsize(video_out)
    print(f"完成！输出: {video_out}")
    print(f"文件大小: {size / 1024 / 1024:.1f} MB")
else:
    print(f"失败:\n{result.stderr}")
