# -*- coding: utf-8 -*-
import subprocess, os

ffmpeg = r'C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe'
BASE = r'C:\Users\Administrator\.openclaw\workspace\workspace-maphot\data'
no_audio = os.path.join(BASE, 'videos', 'shenzhen_v3_no_audio.mp4')
audio_path = os.path.join(BASE, 'audio', 'shenzhen_v3.mp3')
ass_path = os.path.join(BASE, 'cache', 'shenzhen_v3.ass')
final_output = os.path.join(BASE, 'videos', 'shenzhen_v3_final.mp4')

# Use -map and subtitles as input option instead of filter
# First convert ASS to SRT-compatible format for subtitles option
# Or use the -map 0:v -map 1:a -c:v libx264 -vf "subtitles=path" approach

# Try with absolute path but using forward slashes only
abs_ass = ass_path.replace('\\', '/')

# Use the -filter_complex approach
cmd = [
    ffmpeg, '-y',
    '-i', no_audio,
    '-i', audio_path,
    '-c:v', 'libx264',
    '-preset', 'fast',
    '-crf', '18',
    '-pix_fmt', 'yuv420p',
    '-r', '15',
    '-c:a', 'aac',
    '-b:a', '128k',
    '-shortest',
    final_output
]

print("Running without subtitles...")
r = subprocess.run(cmd, capture_output=True, timeout=180)
if r.returncode == 0:
    sz = os.path.getsize(final_output) / 1024
    print(f"OK: {final_output} ({sz:.0f}KB)")
else:
    print(f"FAILED: {r.stderr[-300:].decode('utf-8', errors='replace')}")
