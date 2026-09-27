#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""广州11区GDP排名视频合成 - ffmpeg方案"""
import os
import json
import subprocess
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = r"C:\Users\Administrator\.openclaw\workspace\workspace-maphot"
MAPS_DIR = os.path.join(BASE_DIR, "data", "maps", "20260825")
AUDIO = os.path.join(BASE_DIR, "data", "audio", "city_广州_tts.mp3")
OUTPUT = os.path.join(BASE_DIR, "data", "videos", "city_广州_final.mp4")
FFMPEG = r"C:\ffmpeg-bin\ffmpeg.exe"
FONT = r"C:\Windows\Fonts\msyhbd.ttc"

# 区名顺序（GDP从高到低）
SECTIONS = [
    ("天河区", "7017亿"),
    ("黄埔区", "4346亿"),
    ("越秀区", "3545亿"),
    ("白云区", "3312亿"),
    ("番禺区", "3151亿"),
    ("海珠区", "3136亿"),
    ("南沙区", "2402亿"),
    ("花都区", "1900亿"),
    ("荔湾区", "1300亿"),
    ("增城区", "1100亿"),
    ("从化区", "450亿"),
]

FPS = 30
W, H = 1080, 1920
DUR = 83.5  # 配音时长

# 时间分配：开场5s + 每区7s + 结尾3s
OPENING = 5
PER_SECTION = (DUR - OPENING - 3) / len(SECTIONS)
ENDING = 3

def get_font(size):
    return ImageFont.truetype(FONT, size)

def draw_black_frame():
    img = Image.new("RGB", (W, H), (10, 15, 23))
    return img

def draw_section(map_path, text, subtitle, progress=1.0):
    """绘制一区地图帧"""
    img = Image.new("RGB", (W, H), (10, 15, 23))
    map_img = Image.open(map_path).convert("RGBA")
    
    # 居中缩放
    map_w, map_h = map_img.size
    scale = min(W / map_w, H / map_h) * 0.85
    new_size = (int(map_w * scale), int(map_h * scale))
    map_img = map_img.resize(new_size, Image.Resampling.LANCZOS)
    
    x = (W - new_size[0]) // 2
    y = (H - new_size[1]) // 2 - 100
    
    img.paste(map_img, (x, y), map_img)
    
    # 底部文字
    draw = ImageDraw.Draw(img)
    try:
        title_font = get_font(80)
        num_font = get_font(120)
        sub_font = get_font(50)
    except:
        title_font = ImageFont.load_default()
        num_font = get_font(80)
        sub_font = get_font(50)
    
    cx, cy = W // 2, H - 350
    draw.text((cx, cy), text, fill="#FFFFFF", font=title_font, anchor="mm")
    draw.text((cx, cy + 120), subtitle, fill="#60a5fa", font=num_font, anchor="mm")
    draw.text((cx, cy + 280), "广州市 · 各区GDP", fill="#94a3b8", font=sub_font, anchor="mm")
    
    return img

def render_video():
    print("=" * 50)
    print("广州11区GDP排名 - 视频合成")
    print("=" * 50)
    
    # 获取地图文件
    map_files = sorted([f for f in os.listdir(MAPS_DIR) if f.endswith('.png')])
    print(f"地图文件: {len(map_files)} 张")
    
    # 创建临时目录
    tmp_dir = os.path.join(BASE_DIR, "tmp", "guangzhou_render")
    os.makedirs(tmp_dir, exist_ok=True)
    
    # 生成帧序列
    frames_per_section = int(PER_SECTION * FPS)
    opening_frames = int(OPENING * FPS)
    ending_frames = int(ENDING * FPS)
    total_frames = opening_frames + len(SECTIONS) * frames_per_section + ending_frames
    
    print(f"时间分配: 开场{OPENING}s + 每区{PER_SECTION:.1f}s + 结尾{ENDING}s")
    print(f"总帧数: {total_frames}")
    
    # 开场帧
    for i in range(opening_frames):
        frame = draw_black_frame()
        draw = ImageDraw.Draw(frame)
        try:
            title_font = get_font(100)
            sub_font = get_font(60)
        except:
            title_font = ImageFont.load_default()
            sub_font = get_font(50)
        
        progress = min(1.0, i / (opening_frames * 0.5))
        draw.text((W//2, H//2 - 100), "广州", fill="#FFFFFF", font=title_font, anchor="mm")
        draw.text((W//2, H//2 + 80), f"11个区GDP排名", fill="#60a5fa", font=sub_font, anchor="mm")
        draw.text((W//2, H//2 + 200), "天河7017亿 → 从化450亿", fill="#94a3b8", font=sub_font, anchor="mm")
        frame.save(os.path.join(tmp_dir, f"frame_{i:04d}.jpg"))
    
    # 各区帧
    frame_idx = opening_frames
    for section_idx, (name, gdp) in enumerate(SECTIONS):
        map_file = f"map_{name}.png"
        map_path = os.path.join(MAPS_DIR, map_file)
        
        if not os.path.exists(map_path):
            print(f"警告: 找不到 {map_file}")
            continue
        
        for i in range(frames_per_section):
            frame = draw_section(map_path, name, gdp)
            frame.save(os.path.join(tmp_dir, f"frame_{frame_idx:04d}.jpg"))
            frame_idx += 1
    
    # 结尾帧
    for i in range(ending_frames):
        frame = draw_black_frame()
        draw = ImageDraw.Draw(frame)
        try:
            title_font = get_font(80)
            sub_font = get_font(50)
        except:
            title_font = ImageFont.load_default()
            sub_font = get_font(50)
        
        draw.text((W//2, H//2 - 50), "评论区告诉我你的选择", fill="#FFFFFF", font=title_font, anchor="mm")
        draw.text((W//2, H//2 + 80), "▸", fill="#60a5fa", font=sub_font, anchor="mm")
        frame.save(os.path.join(tmp_dir, f"frame_{frame_idx:04d}.jpg"))
        frame_idx += 1
    
    print(f"帧序列生成完成: {total_frames} 帧")
    
    # 用ffmpeg合成视频
    print("正在渲染视频...")
    cmd = [
        FFMPEG, "-y",
        "-framerate", str(FPS),
        "-i", os.path.join(tmp_dir, "frame_%04d.jpg"),
        "-i", AUDIO,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        OUTPUT
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        size = os.path.getsize(OUTPUT)
        print(f"✓ 视频生成成功: {OUTPUT}")
        print(f"  大小: {size/1024/1024:.1f} MB")
        
        # 获取时长
        probe = subprocess.run([FFMPEG, "-i", OUTPUT], capture_output=True, text=True)
        for line in probe.stderr.split('\n'):
            if "Duration:" in line:
                print(f"  时长: {line.strip()}")
                break
        return True
    else:
        print(f"✗ 渲染失败: {result.stderr[-500:]}")
        return False

if __name__ == "__main__":
    render_video()
