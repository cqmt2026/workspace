# -*- coding: utf-8 -*-
"""
蜗牛幼儿园视频号成品视频生成器 v3.2
功能：从 selected/ 文件夹读取图片，生成9:16竖屏mp4
用法：python video_creator.py [素材文件夹路径] [每帧时长秒]
默认素材: daily_materials/selected/
默认时长: 3秒/张
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r'C:\Users\Administrator\.openclaw\workspace\snail-video')
SELECTED_DIR = BASE / 'daily_materials' / 'selected'
OUTPUT_DIR = BASE / 'daily_materials' / 'output'

IMAGE_EXT = {'.jpg', '.jpeg', '.png', '.webp'}
RESOLUTION = (720, 1280)


def get_image_files(directory):
    if not directory.exists():
        return []
    files = [f for f in directory.iterdir() if f.is_file() and f.suffix.lower() in IMAGE_EXT]
    return sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)


def create_frames(image_files, frames_dir):
    from PIL import Image, ImageDraw, ImageFont

    frames_dir.mkdir(parents=True, exist_ok=True)

    font = None
    for fp in [r'C:\Windows\Fonts\msyh.ttc', r'C:\Windows\Fonts\simhei.ttf']:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, 32)
                break
            except Exception:
                pass
    if font is None:
        font = ImageFont.load_default()

    for i, img_path in enumerate(image_files[:6]):
        img = Image.open(str(img_path))

        ratio = min(RESOLUTION[0] / img.width, RESOLUTION[1] / img.height)
        new_w, new_h = int(img.width * ratio), int(img.height * ratio)
        img = img.resize((new_w, new_h), Image.LANCZOS)

        left = max(0, (new_w - RESOLUTION[0]) // 2)
        top = max(0, (new_h - RESOLUTION[1]) // 2)
        right = min(new_w, left + RESOLUTION[0])
        bottom = min(new_h, top + RESOLUTION[1])
        img = img.crop((left, top, right, bottom))

        w, h = img.size
        if w < RESOLUTION[0] or h < RESOLUTION[1]:
            new_img = Image.new('RGB', RESOLUTION, (0, 0, 0))
            paste_x = (RESOLUTION[0] - w) // 2
            paste_y = (RESOLUTION[1] - h) // 2
            new_img.paste(img, (paste_x, paste_y))
            img = new_img

        draw = ImageDraw.Draw(img)
        bar_h = 80
        draw.rectangle([0, RESOLUTION[1] - bar_h, RESOLUTION[0], RESOLUTION[1]], fill=(0, 0, 0, 180))

        name = img_path.stem.replace('_test', '')
        text = name[:12]
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_x = (RESOLUTION[0] - text_w) // 2
        draw.text((text_x, RESOLUTION[1] - bar_h + 25), text, fill='white', font=font)

        out_path = frames_dir / ('frame_' + str(i).zfill(4) + '.jpg')
        img.save(str(out_path), quality=92)

    return frames_dir


def make_video(frames_dir, output_path, fps=24):
    frame_files = sorted(frames_dir.glob('*.jpg'))
    if not frame_files:
        return False, '没有帧图片'

    # 使用image2序列模式，帧已命名为 frame_0000.jpg ~ frame_NNNN.jpg
    cmd = [
        'ffmpeg', '-y',
        '-framerate', '1',
        '-i', str(frames_dir / 'frame_%04d.jpg'),
        '-vf', 'fps=' + str(fps) + ',scale=' + str(RESOLUTION[0]) + ':' + str(RESOLUTION[1]) + ':force_original_aspect_ratio=decrease,pad=' + str(RESOLUTION[0]) + ':' + str(RESOLUTION[1]) + ':(ow-iw)/2:(oh-ih)/2:black',
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '18',
        '-pix_fmt', 'yuv420p',
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode != 0:
        return False, result.stderr[-500:]
    return True, ''


def main():
    print('=' * 50)
    print('蜗牛幼儿园视频号成品生成器 v3.2')
    print('运行时间: ' + datetime.now().strftime('%Y-%m-%d %H:%M'))
    print('=' * 50)

    input_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else SELECTED_DIR
    duration_per_frame = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    print('输入目录: ' + str(input_dir))
    print('每帧时长: ' + str(duration_per_frame) + '秒')

    image_files = get_image_files(input_dir)
    if not image_files:
        print('\n没有找到图片素材')
        return

    print('\n找到 ' + str(len(image_files)) + ' 张图片:')
    for f in image_files:
        print('  - ' + f.name + ' (' + str(round(f.stat().st_size / 1024, 1)) + 'KB)')

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    frames_dir = OUTPUT_DIR / 'frames' / timestamp
    output_path = OUTPUT_DIR / ('snail_' + timestamp + '.mp4')

    print('\n正在生成...')

    create_frames(image_files, frames_dir)
    print('  已生成 ' + str(len(list(frames_dir.glob('*.jpg')))) + ' 帧图片')

    ok, err = make_video(frames_dir, output_path)
    if not ok:
        print('  视频生成失败: ' + err)
        return

    size_mb = output_path.stat().st_size / 1024 / 1024
    probe_cmd = [
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'csv=p=0', str(output_path)
    ]
    probe = subprocess.run(probe_cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    duration = probe.stdout.strip()

    print('\n视频生成完成！')
    print('文件: ' + str(output_path))
    print('大小: ' + str(round(size_mb, 2)) + ' MB')
    print('时长: ' + duration + 's')
    print('分辨率: ' + str(RESOLUTION[0]) + 'x' + str(RESOLUTION[1]) + ' (9:16竖屏)')
    print('格式: mp4 (H.264)')


if __name__ == '__main__':
    main()