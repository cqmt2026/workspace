# -*- coding: utf-8 -*-
import subprocess, os

ffmpeg = r'C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe'
no_audio = r'C:\Users\Administrator\.openclaw\workspace\workspace-maphot\data\videos\shenzhen_v3_no_audio.mp4'
audio_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-maphot\data\audio\shenzhen_v3.mp3'
srt_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-maphot\data\cache\shenzhen_v3.srt'
final_output = r'C:\Users\Administrator\.openclaw\workspace\workspace-maphot\data\videos\shenzhen_v3_final.mp4'

# 用subtitles选项（不是-vf），放在input后面
cmd = [
    ffmpeg, '-y',
    '-i', no_audio,
    '-i', audio_path,
    '-c:v', 'libx264',
    '-preset', 'fast',
    '-crf', '18',
    '-c:a', 'aac',
    '-b:a', '128k',
    '-vf', f"subtitles='{srt_path.replace(chr(92), '/')}'",
    '-shortest',
    final_output
]

print("Running with subtitles...")
r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
if r.returncode == 0:
    sz = os.path.getsize(final_output) / 1024
    print(f"OK: {final_output} ({sz:.0f}KB, {sz/1024:.1f}MB)")
else:
    print(f"FAILED: {r.stderr[-500:]}")