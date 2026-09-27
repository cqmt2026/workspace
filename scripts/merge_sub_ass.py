# -*- coding: utf-8 -*-
import subprocess, os

ffmpeg = r'C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe'
no_audio = r'C:\Users\Administrator\.openclaw\workspace\workspace-maphot\data\videos\shenzhen_v3_no_audio.mp4'
audio_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-maphot\data\audio\shenzhen_v3.mp3'
srt_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-maphot\data\cache\shenzhen_v3.srt'
final_output = r'C:\Users\Administrator\.openclaw\workspace\workspace-maphot\data\videos\shenzhen_v3_final.mp4'

# Convert SRT to ASS for better encoding support
ass_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-maphot\data\cache\shenzhen_v3.ass'
with open(ass_path, 'w', encoding='utf-8') as f:
    f.write('[Script Info]\n')
    f.write('Title: Shenzhen Video\n')
    f.write('ScriptType: v4.00+\n')
    f.write('PlayResX: 1080\n')
    f.write('PlayResY: 1920\n\n')
    f.write('[V4+ Styles]\n')
    f.write('Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, AlphaTracking\n')
    f.write('Style: Default,Microsoft YaHei,26,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,160,0\n\n')
    f.write('[Events]\n')
    f.write('Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n')
    
    with open(srt_path, 'r', encoding='utf-8') as srt:
        blocks = srt.read().strip().split('\n\n')
        for i, block in enumerate(blocks):
            parts = block.split('\n')
            if len(parts) >= 3:
                time_str = parts[1]
                text = '\n'.join(parts[2:])
                # Convert SRT time to ASS time (HH:MM:CC:SS)
                start_parts = time_str.split(' --> ')[0].strip()
                end_parts = time_str.split(' --> ')[1].strip()
                
                def srt_to_ass(ts):
                    h, m, rest = ts.split(':')
                    s, ms = rest.split(',')
                    sec = int(s) + int(ms)/100.0
                    return f"{h}:{m}:{sec:05.2f}"
                
                start_ass = srt_to_ass(start_parts)
                end_ass = srt_to_ass(end_parts)
                
                f.write(f'Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{text}\n')

print(f"ASS file created: {ass_path}")

# Now use subtitles filter with ASS
cmd = [
    ffmpeg, '-y',
    '-i', no_audio,
    '-i', audio_path,
    '-c:v', 'libx264',
    '-preset', 'fast',
    '-crf', '18',
    '-pix_fmt', 'yuv420p',
    '-r', '15',
    '-vf', f"subtitles='{ass_path.replace(chr(92), '/')}'",
    '-c:a', 'aac',
    '-b:a', '128k',
    '-shortest',
    final_output
]

print("Running...")
r = subprocess.run(cmd, capture_output=True, timeout=300)
if r.returncode == 0:
    sz = os.path.getsize(final_output) / 1024
    print(f"OK: {final_output} ({sz:.0f}KB)")
else:
    err = r.stderr[-1000:] if r.stderr else b''
    with open(r'C:\Users\Administrator\.openclaw\workspace\scripts\ffmpeg_err.txt', 'wb') as f:
        f.write(err)
    print(f"FAILED (see ffmpeg_err.txt)")
