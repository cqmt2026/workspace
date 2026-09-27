# -*- coding: utf-8 -*-
import subprocess, os

ffmpeg = r'C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe'
no_audio = r'C:\Users\Administrator\.openclaw\workspace\workspace-maphot\data\videos\shenzhen_v3_no_audio.mp4'
audio_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-maphot\data\audio\shenzhen_v3.mp3'
srt_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-maphot\data\cache\shenzhen_v3.srt'
final_output = r'C:\Users\Administrator\.openclaw\workspace\workspace-maphot\data\videos\shenzhen_v3_final.mp4'

# Use -vf drawtext with a simpler approach - use shell to escape properly
# First get audio duration
r = subprocess.run([ffmpeg, '-i', audio_path], capture_output=True, text=True, timeout=10)
duration = 146
for line in r.stderr.split('\n'):
    if 'Duration' in line:
        import re
        m = re.search(r'Duration: (\d+):(\d+):(\d+)\.(\d+)', line)
        if m:
            h, mi, s, ms = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
            duration = h * 3600 + mi * 60 + s + ms / 100

# Build drawtext filters manually from SRT
subtitles = []
with open(srt_path, 'r', encoding='utf-8') as f:
    lines = f.read().strip().split('\n\n')
    for block in lines:
        parts = block.split('\n')
        if len(parts) >= 3:
            time_str = parts[1]
            text = '\n'.join(parts[2:])
            start_str, end_str = time_str.split(' --> ')
            
            def parse_ts(ts):
                h, m, rest = ts.split(':')
                s, ms = rest.split(',')
                return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000
            
            start_sec = parse_ts(start_str)
            end_sec = parse_ts(end_str)
            
            # Escape single quotes in text
            escaped = text.replace("'", "\\'")
            subtitles.append(f"drawtext=text='{escaped}':fontfile='C:/Windows/Fonts/msyh.ttc':fontsize=28:fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=8:x=(w-text_w)/2:y=h-168:enable='between(t\\,{start_sec}\\,{end_sec})'")

vf = ','.join(subtitles)

cmd = [
    ffmpeg, '-y',
    '-i', no_audio,
    '-i', audio_path,
    '-c:v', 'libx264',
    '-preset', 'fast',
    '-crf', '18',
    '-pix_fmt', 'yuv420p',
    '-r', '15',
    '-vf', vf,
    '-c:a', 'aac',
    '-b:a', '128k',
    '-t', str(duration),
    '-shortest',
    final_output
]

print(f"Running with {len(subtitles)} subtitle segments...")
r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
if r.returncode == 0:
    sz = os.path.getsize(final_output) / 1024
    print(f"OK: {final_output} ({sz:.0f}KB)")
else:
    print(f"FAILED: {r.stderr[-500:]}")
