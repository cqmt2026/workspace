# -*- coding: utf-8 -*-
"""
平陆运河地理故事流 — 合成脚本
用 Pixabay 空镜素材 + 地图切换 + 配音，生成高质量视频
"""
import os, json, subprocess, shutil

BASE = r'C:\Users\Administrator\.openclaw\workspace\workspace-maphot'
FFMPEG = 'C:\ffmpeg-bin\ffmpeg.exe'
DATA = os.path.join(BASE, 'data')
VIDEOS = os.path.join(DATA, 'videos')
MATS = os.path.join(VIDEOS, '素材')
MAPS = os.path.join(DATA, 'maps', '20260917', 'pinglu_canal_scenes')
AUDIO = os.path.join(DATA, 'audio', 'pinglu_canal_story_tts.mp3')
OUT = os.path.join(VIDEOS, '平陆运河_地理故事流_高质量.mp4')

os.makedirs(os.path.dirname(OUT), exist_ok=True)

# 场景时间轴（秒）：每段地图显示时长 + 空镜过渡
SCENES = [
    # (类型, 时长s, 路径/配置)
    ('map', 12, 'scene1_full_guangxi.png'),     # 广西全貌
    ('bg',  4,  'port_container.mp4'),          # 空镜过渡
    ('map', 12, 'scene2_nanning_start.png'),    # 起点横州
    ('bg',  4,  'port_container.mp4'),          # 空镜过渡
    ('map', 13, 'scene3_crossing.png'),         # 穿越丘陵
    ('bg',  4,  'port_container.mp4'),          # 空镜过渡
    ('map', 13, 'scene4_sea_end.png'),          # 终点茅尾海
    ('bg',  5,  'port_container.mp4'),          # 结尾空镜
]

# 构建 concat 文件列表
tmp_dir = os.path.join(DATA, 'cache', 'pinglu_compose')
os.makedirs(tmp_dir, exist_ok=True)

concat_txt = os.path.join(tmp_dir, 'concat.txt')
segments = []

for i, (stype, dur, path) in enumerate(SCENES):
    if stype == 'map':
        src = os.path.join(MAPS, path)
        if not os.path.exists(src):
            print(f'[ERROR] 地图不存在: {src}')
            exit(1)
        out_seg = os.path.join(tmp_dir, f'seg_{i:02d}.mp4')
        # zoompan: 缓慢放大+平移，持续dur秒
        cmd = [FFMPEG, '-y', '-loop', '1', '-i', src,
               '-t', str(dur),
               '-vf', f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920:guess_original_crop=1,zoompan=z='min(zoom+0.001,1.15)':x='iw/2-(iw/zoom/2)+sin(i*0.02)*50':y='ih/2-(ih/zoom/2)+cos(i*0.015)*30':d={dur*30}:s=1080x1920:fps=30",
               '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
               '-pix_fmt', 'yuv420p', '-r', '30',
               out_seg]
        print(f'[{i}] 处理地图: {path} ({dur}s)')
        r = subprocess.run(cmd, capture_output=True, timeout=60)
        if r.returncode == 0 and os.path.exists(out_seg):
            segments.append(out_seg)
            print(f'  OK: {os.path.getsize(out_seg)//1024}KB')
        else:
            print(f'  FAIL: {r.stderr.decode()[-200:]}')
    else:
        src = os.path.join(MATS, path)
        if not os.path.exists(src):
            print(f'[ERROR] 素材不存在: {src}')
            exit(1)
        out_seg = os.path.join(tmp_dir, f'seg_{i:02d}.mp4')
        cmd = [FFMPEG, '-y', '-i', src, '-t', str(dur),
               '-vf', 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2',
               '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
               '-pix_fmt', 'yuv420p', '-r', '30',
               out_seg]
        print(f'[{i}] 处理空镜: {path} ({dur}s)')
        r = subprocess.run(cmd, capture_output=True, timeout=30)
        if r.returncode == 0 and os.path.exists(out_seg):
            segments.append(out_seg)
            print(f'  OK: {os.path.getsize(out_seg)//1024}KB')

# 拼接所有片段
concat_content = ''.join([f"file '{s.replace(chr(92), '/')}'\n" for s in segments])
with open(concat_txt, 'w', encoding='utf-8') as f:
    f.write(concat_content)

print(f'\n拼接 {len(segments)} 个片段...')
no_audio = os.path.join(tmp_dir, 'no_audio.mp4')
cmd = [FFMPEG, '-y', '-f', 'concat', '-safe', '0', '-i', concat_txt,
       '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
       '-pix_fmt', 'yuv420p', '-r', '30',
       no_audio]
r = subprocess.run(cmd, capture_output=True, timeout=120)
if r.returncode != 0 or not os.path.exists(no_audio):
    print(f'拼接失败: {r.stderr.decode()[-300:]}')
    exit(1)
print(f'画面拼接完成: {os.path.getsize(no_audio)//1024//1024:.1f}MB')

# 获取音频时长
probe = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration',
                        '-of','default=noprint_wrappers=1:nokey=1', AUDIO],
                       capture_output=True, text=True, timeout=10)
audio_dur = float(probe.stdout.strip())
print(f'音频时长: {audio_dur:.1f}s')

# 合成：画面 + 音频
print('合成最终视频...')
cmd = [FFMPEG, '-y', '-i', no_audio, '-i', AUDIO,
       '-c:v', 'copy', '-c:a', 'aac', '-b:a', '128k',
       '-shortest', OUT]
r = subprocess.run(cmd, capture_output=True, timeout=120)
if r.returncode == 0:
    sz = os.path.getsize(OUT)
    print(f'\n[SUCCESS] 视频已保存: {OUT}')
    print(f'  大小: {sz//1024//1024:.1f}MB')
else:
    print(f'合成失败: {r.stderr.decode()[-300:]}')

# 清理临时文件
import shutil as _shutil
try: _shutil.rmtree(tmp_dir)
except: pass
print('\n临时文件已清理')
