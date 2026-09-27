#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速合成 - 每区只生成1帧关键帧，ffmpeg插值"""
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

BASE = r"C:\Users\Administrator\.openclaw\workspace\workspace-maphot"
MAPS = os.path.join(BASE, "data", "maps", "20260825")
AUDIO = os.path.join(BASE, "data", "audio", "city_广州_tts.mp3")
OUTPUT = os.path.join(BASE, "data", "videos", "city_广州_final.mp4")
FFMPEG = r"C:\ffmpeg-bin\ffmpeg.exe"
FONT = r"C:\Windows\Fonts\msyhbd.ttc"
W, H = 1080, 1920
FPS = 30

SECTIONS = [
    ("天河区", "7017亿", "map_天河区.png"),
    ("黄埔区", "4346亿", "map_黄埔区.png"),
    ("越秀区", "3545亿", "map_越秀区.png"),
    ("白云区", "3312亿", "map_白云区.png"),
    ("番禺区", "3151亿", "map_番禺区.png"),
    ("海珠区", "3136亿", "map_海珠区.png"),
    ("南沙区", "2402亿", "map_南沙区.png"),
    ("花都区", "1900亿", "map_花都区.png"),
    ("荔湾区", "1300亿", "map_荔湾区.png"),
    ("增城区", "1100亿", "map_增城区.png"),
    ("从化区", "450亿", "map_从化区.png"),
]

def get_font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except:
        return ImageFont.load_default()

def make_frame(map_path, title, gdp, subtitle=""):
    img = Image.new("RGB", (W, H), (10, 15, 23))
    
    # 添加地图
    if map_path and os.path.exists(map_path):
        m = Image.open(map_path).convert("RGBA")
        s = min(W*0.7/m.width, H*0.5/m.height)
        m = m.resize((int(m.width*s), int(m.height*s)), Image.Resampling.LANCZOS)
        x, y = (W-m.width)//2, (H-m.height)//2 - 150
        img.paste(m, (x, y), m)
    
    # 文字
    d = ImageDraw.Draw(img)
    tf = get_font(90)
    gf = get_font(110)
    sf = get_font(45)
    
    d.text((W//2, H//2 + 200), title, fill="#fff", font=tf, anchor="mm")
    d.text((W//2, H//2 + 320), gdp, fill="#60a5fa", font=gf, anchor="mm")
    if subtitle:
        d.text((W//2, H//2 + 460), subtitle, fill="#94a3b8", font=sf, anchor="mm")
    
    return img

def main():
    # 生成关键帧
    tmp = os.path.join(BASE, "tmp", "frames")
    os.makedirs(tmp, exist_ok=True)
    
    # 开场帧
    make_frame(None, "广州", "11区GDP排名", "天河7017亿 → 从化450亿").save(os.path.join(tmp, "intro.jpg"))
    
    # 各区关键帧
    for name, gdp, fname in SECTIONS:
        make_frame(os.path.join(MAPS, fname), name, gdp).save(os.path.join(tmp, f"{name}.jpg"))
    
    # 结尾帧
    make_frame(None, "你的区排第几?", "", "评论区告诉我").save(os.path.join(tmp, "outro.jpg"))
    
    print("关键帧生成完成")
    
    # ffmpeg合成：开场5s + 每区7s + 结尾3s
    cmd = [
        FFMPEG, "-y",
        "-loop", "1", "-t", "5", "-i", os.path.join(tmp, "intro.jpg"),
        "-loop", "1", "-t", "7", "-i", os.path.join(tmp, "天河区.jpg"),
        "-loop", "1", "-t", "7", "-i", os.path.join(tmp, "黄埔区.jpg"),
        "-loop", "1", "-t", "7", "-i", os.path.join(tmp, "越秀区.jpg"),
        "-loop", "1", "-t", "7", "-i", os.path.join(tmp, "白云区.jpg"),
        "-loop", "1", "-t", "7", "-i", os.path.join(tmp, "番禺区.jpg"),
        "-loop", "1", "-t", "7", "-i", os.path.join(tmp, "海珠区.jpg"),
        "-loop", "1", "-t", "7", "-i", os.path.join(tmp, "南沙区.jpg"),
        "-loop", "1", "-t", "7", "-i", os.path.join(tmp, "花都区.jpg"),
        "-loop", "1", "-t", "7", "-i", os.path.join(tmp, "荔湾区.jpg"),
        "-loop", "1", "-t", "7", "-i", os.path.join(tmp, "增城区.jpg"),
        "-loop", "1", "-t", "7", "-i", os.path.join(tmp, "从化区.jpg"),
        "-loop", "1", "-t", "3", "-i", os.path.join(tmp, "outro.jpg"),
        "-i", AUDIO,
        "-filter_complex", "[0:v][1:v][2:v][3:v][4:v][5:v][6:v][7:v][8:v][9:v][10:v][11:v][12:v]concat=n=13:v=1:a=0[outv]",
        "-map", "[outv]",
        "-map", "13:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        OUTPUT
    ]
    
    print("运行ffmpeg...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        size = os.path.getsize(OUTPUT)
        print(f"✓ 完成: {OUTPUT}")
        print(f"  大小: {size/1024/1024:.1f} MB")
    else:
        print(f"✗ 失败: {r.stderr[-300:]}")

if __name__ == "__main__":
    main()
