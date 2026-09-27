# -*- coding: utf-8 -*-
import subprocess
import os

BASE = r"C:\Users\Administrator\.openclaw\workspace\workspace-maphot"
VIDEO_IN = os.path.join(BASE, "data", "videos", "广州11区GDP排名_最终成品.mp4")
VIDEO_OUT = os.path.join(BASE, "data", "videos", "广州11区GDP排名_带字幕.mp4")
FONT = r"C:\Windows\Fonts\msyh.ttc"

# 用Pillow生成字幕图片序列
from PIL import Image, ImageDraw, ImageFont

# 创建字幕目录
sub_dir = os.path.join(BASE, "data", "videos", "subs")
os.makedirs(sub_dir, exist_ok=True)

# 字幕数据
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

# 生成字幕图片
print("Generating subtitle images...")
for i, (start, end, text) in enumerate(subtitles):
    img = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 加载字体
    try:
        font = ImageFont.truetype(FONT, 60)
    except:
        font = ImageFont.load_default()
    
    # 计算文本位置（底部居中）
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (1080 - text_w) // 2
    y = 1920 - 300
    
    # 绘制阴影
    draw.text((x+3, y+3), text, font=font, fill=(0, 0, 0, 200))
    # 绘制文字
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
    
    # 保存图片
    img_path = os.path.join(sub_dir, f"sub_{i:03d}.png")
    img.save(img_path)
    print(f"  Frame {i}: {start}s-{end}s '{text[:20]}...'")

print(f"Generated {len(subtitles)} subtitle frames")
print(f"Output dir: {sub_dir}")
