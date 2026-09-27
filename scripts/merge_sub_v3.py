# -*- coding: utf-8 -*-
import subprocess, os

ffmpeg = r'C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe'
no_audio = r'C:\Users\Administrator\.openclaw\workspace\workspace-maphot\data\videos\shenzhen_v3_no_audio.mp4'
audio_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-maphot\data\audio\shenzhen_v3.mp3'
srt_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-maphot\data\cache\shenzhen_v3.srt'
final_output = r'C:\Users\Administrator\.openclaw\workspace\workspace-maphot\data\videos\shenzhen_v3_final.mp4'

# subtitles滤镜 + 字体样式
srt_escaped = srt_path.replace('\\', '/')
force_style = "FontName=Microsoft YaHei,FontSize=26,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=0,MarginV=160,Alignment=2"

cmd = [
    ffmpeg, '-y',
    '-i', no_audio,
    '-i', audio_path,
    '-c:v', 'libx264',
    '-preset', 'fast',
    '-crf', '18',
    '-c:a', 'aac',
    '-b:a', '128k',
    '-vf', f"subtitles='{srt_escaped}':fontsdir='C:\\\\Windows\\\\Fonts':force_style='{force_style}'",
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
    # fallback: no subs
    cmd2 = [ffmpeg, '-y', '-i', no_audio, '-i', audio_path,
            '-c:v', 'copy', '-c:a', 'aac', '-b:a', '128k', '-shortest', final_output]
    r2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=60)
    if r2.returncode == 0:
        sz = os.path.getsize(final_output) / 1024
        print(f"OK (no subs): {final_output} ({sz:.0f}KB)")