# -*- coding: utf-8 -*-
import subprocess, sys, os
sys.stdout.reconfigure(encoding='utf-8')

base = r'data/videos/中国贸易朋友圈_v2_完整版.mp4'
pix1 = r'trade-circle/assets/port_container.mp4'
pix2 = r'trade-circle/assets/night_port.mp4'
pix3 = r'trade-circle/assets/shanghai.mp4'
out = r'data/videos/中国贸易朋友圈_素材版.mp4'

# 缩放背景到竖屏
for name, pix, dur in [('bg1', pix1, 12), ('bg2', pix2, 10), ('bg3', pix3, 8)]:
    cmd = ['ffmpeg','-y','-i',pix,'-vf',
           'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1',
           '-t',str(dur),'-c:v','libx264','-preset','fast','-crf','22','-an',
           f'data/videos/{name}.mp4']
    subprocess.run(cmd, capture_output=True, timeout=60)
    sz = os.path.getsize(f'data/videos/{name}.mp4')//1024
    print(f'{name}: {sz} KB')

# 分段
segs = []
# 段1: 0-12s 带bg1
cmd = ['ffmpeg','-y','-i',base,'-i',r'data/videos/bg1.mp4',
       '-filter_complex','[0:v][1:v]overlay=0:0:enable=between(t,0,12)[v]','-map','[v]','-map','0:a:0',
       '-c:v','libx264','-preset','fast','-crf','22','-c:a','aac','-b:a','128k','-t','12',
       r'data/videos/s1.mp4']
r = subprocess.run(cmd, capture_output=True, timeout=120)
segs.append('s1')
print(f's1: {os.path.exists(r"data/videos/s1.mp4")}')

# 段2: 12-22s 带bg2
cmd = ['ffmpeg','-y','-ss','12','-t','10','-i',base,'-i',r'data/videos/bg2.mp4',
       '-filter_complex','[0:v][1:v]overlay=0:0[v]','-map','[v]','-map','0:a:0',
       '-c:v','libx264','-preset','fast','-crf','22','-c:a','aac','-b:a','128k',
       r'data/videos/s2.mp4']
r = subprocess.run(cmd, capture_output=True, timeout=120)
segs.append('s2')
print(f's2: {os.path.exists(r"data/videos/s2.mp4")}')

# 段3: 22-40s 无背景
cmd = ['ffmpeg','-y','-ss','22','-t','18','-i',base,
       '-c:v','libx264','-preset','fast','-crf','22','-c:a','copy',
       r'data/videos/s3.mp4']
r = subprocess.run(cmd, capture_output=True, timeout=120)
segs.append('s3')
print(f's3: {os.path.exists(r"data/videos/s3.mp4")}')

# 段4: 40-48s 带bg3
cmd = ['ffmpeg','-y','-ss','40','-t','8','-i',base,'-i',r'data/videos/bg3.mp4',
       '-filter_complex','[0:v][1:v]overlay=0:0[v]','-map','[v]','-map','0:a:0',
       '-c:v','libx264','-preset','fast','-crf','22','-c:a','aac','-b:a','128k',
       r'data/videos/s4.mp4']
r = subprocess.run(cmd, capture_output=True, timeout=120)
segs.append('s4')
print(f's4: {os.path.exists(r"data/videos/s4.mp4")}')

# 段5: 48-55s 无背景
cmd = ['ffmpeg','-y','-ss','48','-t','7','-i',base,
       '-c:v','libx264','-preset','fast','-crf','22','-c:a','copy',
       r'data/videos/s5.mp4']
r = subprocess.run(cmd, capture_output=True, timeout=120)
segs.append('s5')
print(f's5: {os.path.exists(r"data/videos/s5.mp4")}')

# Concat
with open(r'data/videos/concat.txt','w',encoding='utf-8') as f:
    for s in segs:
        f.write(f"file 'data/videos/{s}.mp4'\n")

cmd = ['ffmpeg','-y','-f','concat','-safe','0','-i',r'data/videos/concat.txt',
       '-c:v','libx264','-preset','medium','-crf','20','-c:a','aac','-b:a','192k', out]
r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
if os.path.exists(out):
    print(f'FINAL: {os.path.getsize(out)//1024//1024} MB')
else:
    print(f'FAIL: {r.stderr[-300:]}')
