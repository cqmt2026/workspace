# -*- coding: utf-8 -*-
"""
平陆运河地理故事流 - 完整流水线
使用 GSAP 动画 + Pixabay 空镜素材 + 4 个场景地图
生成高质量 1080x1920 视频
"""
import os, json, subprocess, shutil

BASE = r'C:\Users\Administrator\.openclaw\workspace\workspace-maphot'
DATA = os.path.join(BASE, 'data')
VIDEOS = os.path.join(DATA, 'videos')
MATS = os.path.join(VIDEOS, '素材')
MAPS_DIR = os.path.join(DATA, 'maps', '20260917', 'pinglu_canal_scenes')
HF_DIR = os.path.join(BASE, 'my-video')
AUDIO = os.path.join(DATA, 'audio', 'pinglu_canal_story_tts.mp3')
OUTPUT = os.path.join(VIDEOS, '平陆运河_地理故事流_hd.mp4')
FFMPEG = r'C:\ffmpeg-bin\ffmpeg.exe'

os.makedirs(HF_DIR, exist_ok=True)
os.makedirs(os.path.join(HF_DIR, 'assets', 'maps'), exist_ok=True)

# ========== 1. 准备素材 ==========
print('[1/5] 准备素材...')

# 复制地图
map_files = ['scene1_full_guangxi.png', 'scene2_nanning_start.png', 'scene3_crossing.png', 'scene4_sea_end.png']
for mf in map_files:
    src = os.path.join(MAPS_DIR, mf)
    dst = os.path.join(HF_DIR, 'assets', 'maps', mf)
    shutil.copy2(src, dst)
    print(f'  {mf}: {os.path.getsize(src)} bytes')

# 复制空镜素材
bg_src = os.path.join(MATS, 'port_container.mp4')
bg_dst = os.path.join(HF_DIR, 'assets', 'bg_port.mp4')
shutil.copy2(bg_src, bg_dst)
print(f'  bg_port.mp4: {os.path.getsize(bg_src)//1024//1024:.1f} MB')

# 复制音频
shutil.copy2(AUDIO, os.path.join(HF_DIR, 'assets', 'audio.mp3'))
print(f'  audio.mp3: {os.path.getsize(AUDIO)//1024} KB')

# ========== 2. 生成 HTML ==========
print('\n[2/5] 生成 HTML...')

html = '''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1080,height=1920">
<title>平陆运河</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { width: 1080px; height: 1920px; overflow: hidden; background: #0A0F1A; font-family: "Microsoft YaHei", sans-serif; }
#root { position: relative; width: 1080px; height: 1920px; }

/* 背景视频层 */
.bg-video { position: absolute; inset: 0; width: 1080px; height: 1920px; object-fit: cover; z-index: 1; }
.bg-overlay { position: absolute; inset: 0; background: rgba(10,15,26,0.7); z-index: 2; }

/* 场景容器 */
.scene { position: absolute; inset: 0; z-index: 10; opacity: 0; visibility: hidden; }
.scene img { width: 1080px; height: 1920px; object-fit: cover; }

/* 文字元素 */
.title-main { position: absolute; top: 8%; left: 0; right: 0; text-align: center; font-size: 72px; font-weight: 700; color: #FFFFFF; letter-spacing: 4px; text-shadow: 0 4px 20px rgba(0,0,0,0.8); }
.title-sub { position: absolute; top: 18%; left: 0; right: 0; text-align: center; font-size: 28px; color: #FFD740; letter-spacing: 2px; }
.badge-big { position: absolute; bottom: 25%; left: 0; right: 0; text-align: center; font-size: 96px; font-weight: 700; color: #00D4FF; text-shadow: 0 0 40px rgba(0,212,255,0.6); }
.badge-unit { position: absolute; bottom: 18%; left: 0; right: 0; text-align: center; font-size: 24px; color: #8899AA; letter-spacing: 2px; }
.info-panel { position: absolute; bottom: 8%; left: 5%; right: 5%; background: rgba(13,21,37,0.95); border: 1px solid #1E3A5F; border-radius: 16px; padding: 20px; }
.info-line { font-size: 22px; color: #FFFFFF; text-align: center; line-height: 1.8; }
.info-highlight { color: #00D4FF; font-weight: 700; }
.info-sub { font-size: 16px; color: #8899AA; text-align: center; margin-top: 8px; }

/* 结尾 */
.outro-title { position: absolute; top: 35%; left: 0; right: 0; text-align: center; font-size: 56px; color: #FFFFFF; font-weight: 700; letter-spacing: 3px; }
.outro-sub { position: absolute; top: 45%; left: 0; right: 0; text-align: center; font-size: 24px; color: #64748B; letter-spacing: 2px; }
.cta-text { position: absolute; bottom: 15%; left: 0; right: 0; text-align: center; font-size: 24px; color: #475569; }
.brand { position: absolute; bottom: 6%; left: 0; right: 0; text-align: center; font-size: 22px; color: #475569; letter-spacing: 7px; }
.brand span { color: #00D4FF; }
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1920" data-duration="60">

<!-- 背景视频 -->
<video class="bg-video" id="bg-video" src="assets/bg_port.mp4" muted playsinline loop></video>
<div class="bg-overlay"></div>

<!-- 场景1: 广西全貌 -->
<div class="scene" id="scene-1">
  <img src="assets/maps/scene1_full_guangxi.png" alt="">
  <div class="title-main">平陆运河</div>
  <div class="title-sub">新中国成立以来第一条江海连通超级运河</div>
  <div class="badge-big">507亿</div>
  <div class="badge-unit">元总投资 · 全长134.2公里</div>
</div>

<!-- 场景2: 起点 -->
<div class="scene" id="scene-2">
  <img src="assets/maps/scene2_nanning_start.png" alt="">
  <div class="title-main">起点：西津渡口</div>
  <div class="title-sub">南宁横州市 · 西江支流</div>
  <div class="badge-big">海拔60m</div>
  <div class="badge-unit">起点高程</div>
</div>

<!-- 场景3: 穿越 -->
<div class="scene" id="scene-3">
  <img src="assets/maps/scene3_crossing.png" alt="">
  <div class="title-main">穿越广西丘陵</div>
  <div class="title-sub">19座梯级船闸 · 逐级提水翻山</div>
  <div class="badge-big">落差19米</div>
  <div class="badge-unit">19座船闸</div>
</div>

<!-- 场景4: 终点 -->
<div class="scene" id="scene-4">
  <img src="assets/maps/scene4_sea_end.png" alt="">
  <div class="title-main">终点：茅尾海</div>
  <div class="title-sub">注入北部湾 · 直通南海</div>
  <div class="badge-big">缩短560km</div>
  <div class="badge-unit">比绕行广州珠江口</div>
</div>

<!-- 结尾 -->
<div class="scene" id="scene-outro">
  <div class="outro-title">一条运河，改的是地理，通的是命运</div>
  <div class="outro-sub">你的省份，离海有多远？</div>
  <div class="cta-text"><span style="font-size:28px">&#9654;</span> 点赞关注，每天看懂地理背后的故事</div>
  <div class="brand"><span>&#128205;</span> 图钉 · 地图热点</div>
</div>

</div>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<script>
window.__timelines = {};
var tl = gsap.timeline({paused: true});

// 启动背景视频
document.getElementById('bg-video').play();

// 场景1: 广西全貌 (0s - 12s)
tl.fromTo("#scene-1", {opacity:0}, {opacity:1, duration:0.4, ease:"power2.out"}, 0);
tl.fromTo("#scene-1 .title-main", {y:-40, opacity:0}, {y:0, opacity:1, duration:0.5, ease:"power2.out"}, 0.3);
tl.fromTo("#scene-1 .title-sub", {y:20, opacity:0}, {y:0, opacity:1, duration:0.4, ease:"power2.out"}, 0.6);
tl.fromTo("#scene-1 .badge-big", {scale:0.5, opacity:0}, {scale:1, opacity:1, duration:0.5, ease:"back.out(1.5)"}, 1.0);
tl.fromTo("#scene-1 .badge-unit", {y:10, opacity:0}, {y:0, opacity:1, duration:0.3, ease:"power2.out"}, 1.5);
tl.to("#scene-1", {opacity:0, duration:0.3, ease:"power2.in"}, 11.5);
tl.set("#scene-1", {visibility:"hidden"}, 11.8);

// 场景2: 起点 (12s - 24s)
tl.fromTo("#scene-2", {opacity:0}, {opacity:1, duration:0.4, ease:"power2.out"}, 12);
tl.fromTo("#scene-2 .title-main", {y:-40, opacity:0}, {y:0, opacity:1, duration:0.5, ease:"power2.out"}, 12.3);
tl.fromTo("#scene-2 .title-sub", {y:20, opacity:0}, {y:0, opacity:1, duration:0.4, ease:"power2.out"}, 12.6);
tl.fromTo("#scene-2 .badge-big", {scale:0.5, opacity:0}, {scale:1, opacity:1, duration:0.5, ease:"back.out(1.5)"}, 13);
tl.fromTo("#scene-2 .badge-unit", {y:10, opacity:0}, {y:0, opacity:1, duration:0.3, ease:"power2.out"}, 13.5);
tl.to("#scene-2", {opacity:0, duration:0.3, ease:"power2.in"}, 23.5);
tl.set("#scene-2", {visibility:"hidden"}, 23.8);

// 场景3: 穿越 (24s - 38s)
tl.fromTo("#scene-3", {opacity:0}, {opacity:1, duration:0.4, ease:"power2.out"}, 24);
tl.fromTo("#scene-3 .title-main", {y:-40, opacity:0}, {y:0, opacity:1, duration:0.5, ease:"power2.out"}, 24.3);
tl.fromTo("#scene-3 .title-sub", {y:20, opacity:0}, {y:0, opacity:1, duration:0.4, ease:"power2.out"}, 24.6);
tl.fromTo("#scene-3 .badge-big", {scale:0.5, opacity:0}, {scale:1, opacity:1, duration:0.5, ease:"back.out(1.5)"}, 25);
tl.fromTo("#scene-3 .badge-unit", {y:10, opacity:0}, {y:0, opacity:1, duration:0.3, ease:"power2.out"}, 25.5);
tl.to("#scene-3", {opacity:0, duration:0.3, ease:"power2.in"}, 37.5);
tl.set("#scene-3", {visibility:"hidden"}, 37.8);

// 场景4: 终点 (38s - 50s)
tl.fromTo("#scene-4", {opacity:0}, {opacity:1, duration:0.4, ease:"power2.out"}, 38);
tl.fromTo("#scene-4 .title-main", {y:-40, opacity:0}, {y:0, opacity:1, duration:0.5, ease:"power2.out"}, 38.3);
tl.fromTo("#scene-4 .title-sub", {y:20, opacity:0}, {y:0, opacity:1, duration:0.4, ease:"power2.out"}, 38.6);
tl.fromTo("#scene-4 .badge-big", {scale:0.5, opacity:0}, {scale:1, opacity:1, duration:0.5, ease:"back.out(1.5)"}, 39);
tl.fromTo("#scene-4 .badge-unit", {y:10, opacity:0}, {y:0, opacity:1, duration:0.3, ease:"power2.out"}, 39.5);
tl.to("#scene-4", {opacity:0, duration:0.3, ease:"power2.in"}, 49.5);
tl.set("#scene-4", {visibility:"hidden"}, 49.8);

// 结尾 (50s - 60s)
tl.fromTo("#scene-outro", {yPercent:50, opacity:0}, {yPercent:0, opacity:1, duration:0.6, ease:"power3.out"}, 50);
tl.fromTo("#scene-outro .outro-title", {y:-30, scale:0.5, opacity:0}, {y:0, scale:1, opacity:1, duration:0.5, ease:"back.out(1.5)"}, 50.5);
tl.fromTo("#scene-outro .outro-sub", {y:15, opacity:0}, {y:0, opacity:1, duration:0.3, ease:"power2.out"}, 51.2);
tl.fromTo("#scene-outro .cta-text", {y:10, opacity:0}, {y:0, opacity:1, duration:0.3, ease:"power2.out"}, 52);
tl.fromTo("#scene-outro .brand", {y:15, opacity:0}, {y:0, opacity:1, duration:0.3, ease:"power2.out"}, 53.5);

window.__timelines["main"] = tl;
tl.play();
</script>
</body>
</html>'''

html_path = os.path.join(HF_DIR, 'index.html')
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f'  HTML: {len(html)} bytes')

# ========== 3. 渲染视频 ==========
print('\n[3/5] 渲染视频（约3分钟）...')
cmd = ['npx', 'hyperframes@0.8.17', 'render', '--quality', 'standard', '--output', 'pinglu_canal_hd.mp4']
r = subprocess.run(cmd, cwd=HF_DIR, capture_output=True, text=True, timeout=300)
if r.returncode != 0:
    print(f'  [ERROR] 渲染失败:\n{r.stderr[-500:]}')
    exit(1)

rendered = os.path.join(HF_DIR, 'pinglu_canal_hd.mp4')
if not os.path.exists(rendered):
    print('  [ERROR] 渲染输出文件不存在')
    exit(1)

print(f'  渲染完成: {os.path.getsize(rendered)//1024//1024:.1f} MB')

# ========== 4. 复制到输出目录 ==========
print('\n[4/5] 复制输出文件...')
shutil.copy2(rendered, OUTPUT)
sz = os.path.getsize(OUTPUT)
print(f'  输出: {OUTPUT}')
print(f'  大小: {sz//1024//1024:.1f} MB')

# ========== 5. 统计 ==========
print('\n[5/5] 完成!')
print(f'  时长: 60秒')
print(f'  分辨率: 1080×1920')
print(f'  场景: 广西全貌 → 起点 → 穿越 → 终点 → 结尾')
print(f'  素材: 4张地图 + 1段港口空镜 + 配音')
