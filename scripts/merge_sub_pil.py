# -*- coding: utf-8 -*-
"""Use PIL to overlay subtitles on each frame, then re-encode with ffmpeg."""
import subprocess, os, tempfile
from PIL import Image, ImageDraw, ImageFont

ffmpeg = r'C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe'
BASE = r'C:\Users\Administrator\.openclaw\workspace\workspace-maphot\data'
no_audio = os.path.join(BASE, 'videos', 'shenzhen_v3_no_audio.mp4')
audio_path = os.path.join(BASE, 'audio', 'shenzhen_v3.mp3')
srt_path = os.path.join(BASE, 'cache', 'shenzhen_v3.srt')
final_output = os.path.join(BASE, 'videos', 'shenzhen_v3_final.mp4')

# Extract all frames
frames_dir = os.path.join(BASE, 'cache', 'sub_frames')
os.makedirs(frames_dir, exist_ok=True)
extract_cmd = [ffmpeg, '-y', '-i', no_audio, '-vf', 'fps=15', os.path.join(frames_dir, 'frame_%04d.png')]
r = subprocess.run(extract_cmd, capture_output=True, timeout=300)
if r.returncode != 0:
    print(f"Extract failed: {r.stderr.decode('utf-8', errors='replace')[-200:]}")
    exit(1)
print("Frames extracted")

# Load subtitles
subtitles = []
with open(srt_path, 'r', encoding='utf-8') as f:
    blocks = f.read().strip().split('\n\n')
    for block in blocks:
        parts = block.split('\n')
        if len(parts) >= 3:
            time_str = parts[1]
            text = '\n'.join(parts[2:])
            start_str, end_str = time_str.split(' --> ')
            def parse_ts(ts):
                h, m, rest = ts.split(':')
                s, ms = rest.split(',')
                return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000
            subtitles.append((parse_ts(start_str), parse_ts(end_str), text.strip()))

# Font
font_path = r'C:\Windows\Fonts\msyh.ttc'
font = ImageFont.truetype(font_path, 28)

# Get frame count
frame_files = sorted([f for f in os.listdir(frames_dir) if f.endswith('.png')])
total_frames = len(frame_files)
fps = 15
print(f"Total frames: {total_frames}")

# Overlay subtitles
font_height = font.getbbox('测试')[3] - font.getbbox('测试')[1]
for i, fname in enumerate(frame_files):
    t = i / fps
    frame_path = os.path.join(frames_dir, fname)
    img = Image.open(frame_path)
    draw = ImageDraw.Draw(img)
    
    # Find subtitles active at this time
    for start_t, end_t, text in subtitles:
        if start_t <= t < end_t:
            # Wrap text
            lines = []
            current_line = ''
            # Estimate character width (Chinese ~30px, ASCII ~15px)
            max_w = 1000  # leave margins
            for char in text:
                bbox = font.getbbox(char)
                char_w = bbox[2] - bbox[0]
                if len(current_line) > 0 and char_w + sum(font.getbbox(c)[2] for c in current_line) > max_w:
                    lines.append(current_line)
                    current_line = char
                else:
                    current_line += char
            if current_line:
                lines.append(current_line)
            
            # Center vertically above bottom
            total_h = len(lines) * (font_height + 4)
            start_y = img.height - 168 - total_h
            
            for j, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line, font=font)
                tw = bbox[2] - bbox[0]
                x = (img.width - tw) // 2
                y = start_y + j * (font_height + 4)
                
                # Shadow/outline
                draw.text((x+1, y+1), line, font=font, fill='#000000')
                draw.text((x, y), line, font=font, fill='#FFFFFF')
                break  # Only render the last active subtitle
            break
    
    img.save(frame_path)

print("Subtitles overlayed")

# Re-encode
tmp_video = os.path.join(frames_dir, 'temp.mp4')
cmd = [
    ffmpeg, '-y',
    '-framerate', '15',
    '-i', os.path.join(frames_dir, 'frame_%04d.png'),
    '-c:v', 'libx264',
    '-preset', 'fast',
    '-crf', '18',
    '-pix_fmt', 'yuv420p',
    tmp_video
]
r = subprocess.run(cmd, capture_output=True, timeout=300)
if r.returncode != 0:
    print(f"Re-encode failed: {r.stderr.decode('utf-8', errors='replace')[-200:]}")
else:
    print(f"Video re-encoded: {tmp_video}")

# Merge with audio
cmd2 = [
    ffmpeg, '-y',
    '-i', tmp_video,
    '-i', audio_path,
    '-c:v', 'copy',
    '-c:a', 'aac',
    '-b:a', '128k',
    '-shortest',
    final_output
]
r2 = subprocess.run(cmd2, capture_output=True, timeout=180)
if r2.returncode == 0:
    sz = os.path.getsize(final_output) / 1024
    print(f"OK: {final_output} ({sz:.0f}KB)")
else:
    print(f"Merge failed: {r2.stderr.decode('utf-8', errors='replace')[-200:]}")

# Cleanup
import shutil
shutil.rmtree(frames_dir, ignore_errors=True)
os.remove(tmp_video)
print("Done")
