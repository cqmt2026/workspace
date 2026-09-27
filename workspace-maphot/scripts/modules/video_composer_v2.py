# -*- coding: utf-8 -*-
"""
Video Composer v2 - 视频合成模块（支持地图动态动画）
在每段地图上叠加动态标注效果：
- 点位弹入（从小到大，从透明到不透明）
- 飞线动画（从起点到终点画线）
- 数字滚动（数据从0滚到目标值）
- 文字渐入

核心：PIL 生成多帧动画序列 → FFmpeg 合成视频段 → concat 拼接
"""

import os
import json
import subprocess
import logging
import tempfile
import math
import re
import numpy as np
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VIDEO_CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'video_config.json')
VIDEO_DIR = os.path.join(BASE_DIR, 'data', 'videos')


def load_video_config():
    with open(VIDEO_CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


class VideoComposerV2:
    """视频合成器v2：支持地图动态标注动画"""

    def __init__(self):
        self.config = load_video_config()
        self.output_dir = VIDEO_DIR
        os.makedirs(self.output_dir, exist_ok=True)
        self.font_path = 'C:/Windows/Fonts/msyhbd.ttc'

    def compose(self, script_path, map_paths=None, audio_path=None,
                output_path=None, bgm_path=None, bgm_volume=0.3,
                animations=None):
        """
        合成视频（支持动态地图动画）

        Args:
            script_path: 脚本JSON路径
            map_paths: 地图图片路径列表
            audio_path: 配音MP3路径
            output_path: 输出视频路径
            bgm_path: BGM路径
            bgm_volume: BGM音量
            animations: 每段动画配置列表，格式：
                [{
                    "type": "dot_pop" | "fly_line" | "number_roll" | "text_fade",
                    "points": [{"x": x_px, "y": y_px, "name": "名称", "color": (r,g,b)}],
                    "lines": [{"from": (x1,y1), "to": (x2,y2)}],
                    "data_value": "1.5万",
                    "text": "字幕文字",
                }, ...]

        Returns:
            输出视频路径
        """
        with open(script_path, 'r', encoding='utf-8') as f:
            script = json.load(f)

        title = script.get('title', 'video')
        sections = script.get('sections', [])

        if isinstance(map_paths, str):
            map_paths = [map_paths]

        audio_duration = self._get_audio_duration(audio_path)
        if audio_duration <= 0:
            logger.error("音频时长无效")
            return None

        if not output_path:
            output_path = os.path.join(self.output_dir,
                                       f"{datetime.now().strftime('%Y%m%d')}_{title}.mp4")

        fps = self.config['output'].get('fps', 15)
        resolution = self.config['output'].get('resolution', '1080x1920')
        width, height = [int(x) for x in resolution.split('x')]
        font_size = self.config['subtitle'].get('font_size', 36)

        num_segments = max(len(sections), len(map_paths), 1)
        seg_duration = audio_duration / num_segments

        # 准备帧文件列表
        frame_files = []
        for idx in range(num_segments):
            mp = map_paths[idx] if idx < len(map_paths) else (map_paths[-1] if map_paths else None)
            if mp and os.path.exists(mp):
                frame_files.append(mp)

        if not frame_files:
            logger.error("没有可用地图帧")
            return None

        temp_dir = os.path.join(tempfile.gettempdir(),
                                f'hf_v2_{datetime.now().strftime("%H%M%S")}')
        os.makedirs(temp_dir, exist_ok=True)

        # 构建字幕列表
        subtitle_texts = []
        for idx in range(num_segments):
            if idx == 0:
                txt = script.get('title', '')
            elif idx <= len(sections):
                sec = sections[idx - 1]
                txt = sec.get('data_point', '') or sec.get('narration', '')[:30]
            else:
                txt = script.get('outro', {}).get('text', '')
            if len(txt) > 60:
                txt = txt[:57] + '...'
            subtitle_texts.append(txt)

        # 提取数据值用于数字动画
        data_values = []
        for idx in range(num_segments):
            if idx == 0:
                data_values.append("")
            elif idx <= len(sections):
                sec = sections[idx - 1]
                dp = sec.get('data_point', '')
                nums = re.findall(r'[\d.]+', dp)
                if nums:
                    unit = re.search(r'[^\d.]+', dp)
                    unit_str = unit.group(0) if unit else ''
                    data_values.append((float(nums[0]), unit_str, dp))
                else:
                    data_values.append("")
            else:
                data_values.append("")

        # ====== 逐段生成动画帧 ======
        temp_segments = []

        for idx, frame_file in enumerate(frame_files):
            seg_frames = max(int(seg_duration * fps), 1)
            seg_out = os.path.join(temp_dir, f'seg_{idx:04d}.mp4')

            # 加载底图
            base_img = Image.open(frame_file).convert('RGBA')
            base_img = base_img.resize((width, height), Image.LANCZOS)

            # 生成帧序列
            frame_dir = os.path.join(temp_dir, f'frames_{idx:04d}')
            os.makedirs(frame_dir, exist_ok=True)

            for f_idx in range(seg_frames):
                progress = f_idx / max(seg_frames - 1, 1)  # 0.0 → 1.0
                frame = base_img.copy()
                draw = ImageDraw.Draw(frame)

                # ---- 1. 字幕（始终显示） ----
                sub_txt = subtitle_texts[idx] if idx < len(subtitle_texts) else ''
                if sub_txt:
                    try:
                        font = ImageFont.truetype(self.font_path, font_size)
                    except:
                        font = ImageFont.load_default()
                    bbox = draw.textbbox((0, 0), sub_txt, font=font)
                    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                    sub_x = (width - tw) // 2
                    sub_y = height - th - 120
                    pad = 10
                    draw.rectangle([sub_x - pad, sub_y - pad, sub_x + tw + pad, sub_y + th + pad],
                                   fill=(0, 0, 0, 180))
                    draw.text((sub_x, sub_y), sub_txt, fill=(255, 255, 255), font=font)

                # ---- 2. 数据大号数字动画（从0滚到目标值） ----
                dv = data_values[idx] if idx < len(data_values) else ""
                if dv and isinstance(dv, tuple):
                    target_num, unit_str, raw_dp = dv
                    current_num = target_num * progress
                    # 格式化数字
                    if target_num >= 10000:
                        display = f"{current_num:.0f}{unit_str}"
                    elif target_num >= 100:
                        display = f"{current_num:.0f}{unit_str}"
                    elif target_num >= 1:
                        display = f"{current_num:.1f}{unit_str}"
                    else:
                        display = f"{current_num:.2f}{unit_str}"

                    try:
                        big_font = ImageFont.truetype(self.font_path, 120)
                    except:
                        big_font = ImageFont.load_default()
                    bbox2 = draw.textbbox((0, 0), display, font=big_font)
                    tw2, th2 = bbox2[2] - bbox2[0], bbox2[3] - bbox2[1]
                    x2 = (width - tw2) // 2
                    y2 = height // 3
                    pad2 = 20
                    # 数字从透明到不透明
                    alpha = int(progress * 255)
                    draw.rectangle([x2 - pad2, y2 - pad2, x2 + tw2 + pad2, y2 + th2 + pad2],
                                   fill=(0, 0, 0, int(120 * progress)))
                    draw.text((x2, y2), display, fill=(255, 60, 60, alpha), font=big_font)

                # ---- 3. 点位弹入动画 ----
                if animations and idx < len(animations):
                    anim = animations[idx]
                    # 点位弹入
                    points = anim.get('points', [])
                    for pt in points:
                        px, py = pt.get('x', 0), pt.get('y', 0)
                        name = pt.get('name', '')
                        color = pt.get('color', (255, 60, 60))
                        # 弹入：从0到1的缩放
                        pop_progress = min(progress * 2, 1.0)  # 前半段时间弹入
                        if pop_progress > 0:
                            radius = max(int(8 * pop_progress), 1)
                            # 外圈光晕
                            for r_mult in [3, 2, 1]:
                                r_val = radius * r_mult
                                alpha_val = int(80 * pop_progress * (1 - r_val / max(radius * 3, 1)))
                                if alpha_val > 0:
                                    draw.ellipse([px - r_val, py - r_val, px + r_val, py + r_val],
                                                 fill=(*color, alpha_val))
                            # 主点
                            draw.ellipse([px - radius, py - radius, px + radius, py + radius],
                                         fill=(*color, 255))
                            draw.ellipse([px - radius // 2, py - radius // 2,
                                          px + radius // 2, py + radius // 2],
                                         fill=(255, 255, 255, 255))

                    # 飞线动画
                    lines = anim.get('lines', [])
                    for line in lines:
                        fx, fy = line.get('from', (0, 0))
                        tx, ty = line.get('to', (0, 0))
                        # 飞线从起点到终点
                        line_progress = min(progress * 1.5, 1.0)
                        if line_progress > 0:
                            # 贝塞尔曲线控制点（向上弯曲）
                            cx = (fx + tx) / 2
                            cy = (fy + ty) / 2 - 100
                            # 采样点
                            num_samples = 50
                            for t_idx in range(num_samples):
                                t = t_idx / num_samples
                                if t > line_progress:
                                    break
                                bx = (1 - t) ** 2 * fx + 2 * (1 - t) * t * cx + t ** 2 * tx
                                by = (1 - t) ** 2 * fy + 2 * (1 - t) * t * cy + t ** 2 * ty
                                # 头亮尾暗
                                head_alpha = int(255 * (1 - abs(t - line_progress) * 3))
                                if head_alpha > 0:
                                    draw.ellipse([int(bx) - 2, int(by) - 2, int(bx) + 2, int(by) + 2],
                                                 fill=(255, 215, 0, min(head_alpha, 255)))

                # 保存帧
                frame_path = os.path.join(frame_dir, f'frame_{f_idx:05d}.png')
                frame.save(frame_path)

            # 用 FFmpeg 合成该段视频
            frame_pattern = os.path.join(frame_dir, 'frame_%05d.png').replace('\\', '/')
            seg_cmd = [
                'ffmpeg', '-y',
                '-framerate', str(fps),
                '-i', frame_pattern,
                '-c:v', 'libx264', '-preset', 'ultrafast',
                '-crf', str(self.config['output'].get('crf', 20)),
                '-pix_fmt', 'yuv420p',
                '-vf', f'scale={width}:{height}',
                seg_out
            ]
            r = subprocess.run(seg_cmd, capture_output=True, text=False, timeout=120)
            if r.returncode == 0 and os.path.exists(seg_out):
                temp_segments.append(seg_out)
                logger.info(f"  分段{idx}动画完成 ({seg_frames}帧)")
            else:
                err = r.stderr[-300:].decode('utf-8', errors='replace') if r.stderr else ''
                logger.warning(f"分段{idx}合成失败: {err}")
                # 回退：用原始地图直接zoompan
                fallback_out = os.path.join(temp_dir, f'seg_fb_{idx:04d}.mp4')
                seg_zoom_end = 1.03
                seg_zoom_step = (seg_zoom_end - 1.0) / max(seg_frames, 1)
                filter_str = (
                    f'zoompan=z=if(lte(zoom\\,{seg_zoom_end})\\,zoom+{seg_zoom_step}\\,{seg_zoom_end}):'
                    f'd={seg_frames}:x=iw/2-(iw/zoom/2):y=ih/2-(ih/zoom/2):s={width}x{height}[v]'
                )
                fb_cmd = [
                    'ffmpeg', '-y', '-loop', '1', '-i', frame_file,
                    '-filter_complex', filter_str,
                    '-map', '[v]', '-c:v', 'libx264', '-preset', 'ultrafast',
                    '-crf', str(self.config['output'].get('crf', 20)),
                    '-pix_fmt', 'yuv420p', '-t', str(seg_duration), fallback_out
                ]
                subprocess.run(fb_cmd, capture_output=True, timeout=60)
                if os.path.exists(fallback_out):
                    temp_segments.append(fallback_out)

        if not temp_segments:
            logger.error("所有分段失败")
            return None

        # ====== concat 拼接 + 音频 ======
        concat_file = os.path.join(temp_dir, 'concat.txt')
        with open(concat_file, 'w', encoding='utf-8') as f:
            for seg in temp_segments:
                f.write(f"file '{seg.replace('\\\\', '/')}'\n")

        if bgm_path and os.path.exists(bgm_path):
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat', '-safe', '0', '-i', concat_file,
                '-i', audio_path, '-i', bgm_path,
                '-filter_complex',
                f'[1:a]volume=1.0[a_main];[2:a]volume={bgm_volume}[a_bgm];'
                f'[a_main][a_bgm]amix=inputs=2:duration=first[a_out]',
                '-map', '0:v', '-map', '[a_out]',
                '-c:v', 'libx264', '-preset', 'fast',
                '-crf', str(self.config['output'].get('crf', 20)),
                '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k',
                '-shortest', output_path
            ]
        else:
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat', '-safe', '0', '-i', concat_file,
                '-i', audio_path,
                '-c:v', 'libx264', '-preset', 'fast',
                '-crf', str(self.config['output'].get('crf', 20)),
                '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k',
                '-shortest', output_path
            ]

        logger.info(f"最终合成（{len(temp_segments)}段, 动画帧）...")
        result = subprocess.run(cmd, capture_output=True, text=False, timeout=600)

        # 清理
        for seg in temp_segments:
            try:
                if os.path.exists(seg):
                    os.remove(seg)
            except:
                pass
        try:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass

        if result.returncode == 0 and os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"视频合成成功: {output_path} ({size_mb:.1f}MB, {len(temp_segments)}段)")
            return output_path
        else:
            try:
                err = result.stderr[-1000:].decode('utf-8', errors='replace')
            except:
                err = 'unknown'
            logger.error(f"视频合成失败: {err}")
            return None

    def _get_audio_duration(self, audio_path):
        if not audio_path or not os.path.exists(audio_path):
            return 0
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
               '-of', 'default=noprint_wrappers=1:nokey=1', audio_path]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return float(r.stdout.strip())
        except:
            return 0