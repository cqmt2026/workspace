# -*- coding: utf-8 -*-
import subprocess, sys, os
sys.stdout.reconfigure(encoding='utf-8')

segs = ['s1','s2','s3','s4','s5']
concat = r'data/videos/concat.txt'
out = r'data/videos/中国贸易朋友圈_素材版.mp4'

with open(concat, 'w', encoding='utf-8') as f:
    for s in segs:
        f.write("file 'data/videos/%s.mp4'\n" % s)

print("Concat file:")
with open(concat, 'r', encoding='utf-8') as f:
    print(f.read())

cmd = ['ffmpeg','-y','-f','concat','-safe','0','-i', concat,
       '-c:v','libx264','-preset','medium','-crf','20','-c:a','aac','-b:a','192k', out]
r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
if os.path.exists(out):
    print('FINAL: OK - %d MB' % (os.path.getsize(out)//1024//1024))
    for s in segs:
        sz = os.path.getsize('data/videos/%s.mp4' % s)//1024//1024
        print('  %s: %d MB' % (s, sz))
else:
    print('FINAL: FAIL')
    print(r.stderr[-400:])
