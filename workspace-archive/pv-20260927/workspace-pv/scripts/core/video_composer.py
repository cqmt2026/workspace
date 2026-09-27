# -*- coding: utf-8 -*-
"""
光伏获客系统 — 视频合成v0.5
改进：优先使用本地素材库，支持品牌元素叠加
"""
import sys, os
sys.path.insert(0, r'C:\Users\Administrator\.openclaw\workspace\workspace-pv\scripts')
os.chdir(r'C:\Users\Administrator\.openclaw\workspace\workspace-pv')

from pathlib import Path
from datetime import datetime
import json
import subprocess
import tempfile
import re
import shutil
import random

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = ImageDraw = ImageFont = None

_has_edge_tts = False
try:
    import edge_tts
    _has_edge_tts = True
except ImportError:
    pass


class PVVideoComposer:
    """PV内容视频合成器 v0.5 — 素材库+品牌元素"""
    
    # 主题-图库映射
    THEME_IMAGE_MAP = {
        "benefit": ["roof_solar", "solar_panel"],
        "policy": ["company", "installation"],
        "news": ["solar_farm", "roof_solar"],
        "tech": ["solar_panel", "inverter"],
        "avoid": ["installation", "inverter"],
    }
    
    COLORS = {
        'title': (255, 210, 60),
        'body': (255, 255, 255),
        'cta': (80, 200, 255),
        'brand': (140, 140, 140),
        'highlight': (255, 100, 100),
        'accent': (100, 180, 255),
        'dark_bg': (12, 18, 35),
        'card_bg': (25, 35, 60),
        'grid': (40, 55, 80),
    }
    
    def __init__(self):
        self.base = Path(__file__).parent.parent.parent
        self.output_dir = self.base / "data" / "videos"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir = self.base / "data" / "assets"
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.photos_dir = self.assets_dir / "photos"
        self.logos_dir = self.assets_dir / "logos"
        self.width = 1080
        self.height = 1920
        self.fps = 15
        self.font_path = "C:/Windows/Fonts/msyhbd.ttc"
        self._image_cache = {}
        
        # 加载品牌配置
        self._load_brand_config()
    
    def _load_brand_config(self):
        """加载品牌配置"""
        config_path = self.assets_dir / "brand.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self.brand = json.load(f)
        else:
            self.brand = {
                "name": "九箭新能源",
                "slogan": "专业光伏获客方案",
                "primary_color": "#FF6B00",
                "secondary_color": "#1E3A5F",
            }
    
    def _get_font(self, size):
        if ImageFont is None:
            return None
        try:
            return ImageFont.truetype(self.font_path, size)
        except:
            return ImageFont.load_default()
    
    def _text_to_lines(self, text, max_chars=30):
        return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]
    
    def _get_bg_image(self, theme_keyword):
        """从素材库获取背景图"""
        # 确定搜索目录
        search_dirs = self.THEME_IMAGE_MAP.get(theme_keyword, ["roof_solar", "solar_farm"])
        
        for dir_name in search_dirs:
            photo_dir = self.photos_dir / dir_name
            if photo_dir.exists():
                photos = list(photo_dir.glob("*.jpg")) + list(photo_dir.glob("*.png"))
                if photos:
                    return random.choice(photos)
        
        return None
    
    def _draw_bg_pattern(self, draw, w, h):
        """绘制科技网格背景"""
        for y in range(0, h, 3):
            ratio = y / h
            r = int(12 + ratio * 15)
            g = int(18 + ratio * 20)
            b = int(35 + ratio * 30)
            draw.line([(0, y), (w, y)], fill=(r, g, b))
        
        grid_color = self.COLORS['grid']
        spacing = 60
        for x in range(0, w, spacing):
            draw.line([(x, 0), (x, h)], fill=(*grid_color, 30), width=1)
        for y in range(0, h, spacing):
            draw.line([(0, y), (w, y)], fill=(*grid_color, 30), width=1)
    
    def _render_slide(self, title, body, cta, bg_path=None, extra=None):
        """渲染单帧幻灯片"""
        if Image is None:
            return None
        
        w, h = self.width, self.height
        img = Image.new('RGBA', (w, h), (*self.COLORS['dark_bg'], 255))
        draw = ImageDraw.Draw(img)
        
        # 绘制背景
        self._draw_bg_pattern(draw, w, h)
        
        # 叠加背景图
        if bg_path and os.path.exists(bg_path):
            try:
                bg = Image.open(bg_path).convert('RGBA')
                bg = bg.resize((w, h), Image.Resampling.LANCZOS)
                overlay = Image.new('RGBA', (w, h), (*self.COLORS['dark_bg'], int(255 * 0.65)))
                bg = Image.alpha_composite(bg, overlay)
                img.paste(bg, (0, 0), bg)
            except:
                pass
        
        # 顶部品牌条
        draw.rectangle([0, 0, w, 70], fill=(8, 12, 25))
        brand_font = self._get_font(22)
        draw.text((30, 15), f"{self.brand.get('name', '九箭新能源')} · 光伏获客系统", 
                  fill=(180, 180, 180), font=brand_font)
        draw.line([(50, 70), (w-50, 70)], fill=self.COLORS['accent'], width=2)
        
        # 标题
        title_font = self._get_font(54)
        title_text = title[:25] if len(title) > 25 else title
        title_lines = self._text_to_lines(title_text, 22)
        for i, line in enumerate(title_lines):
            bbox = draw.textbbox((0, 0), line, font=title_font)
            tw = bbox[2] - bbox[0]
            x = (w-tw)//2
            y = 130 + i*70
            draw.text((x+2, y+2), line, fill=(180, 140, 0), font=title_font)
            draw.text((x, y), line, fill=self.COLORS['title'], font=title_font)
        if title_lines:
            last_line = title_lines[-1]
            bbox = draw.textbbox((0, 0), last_line, font=title_font)
            tw = bbox[2] - bbox[0]
            x = (w-tw)//2
            draw.line([(x, y+65), (x+tw, y+65)], fill=self.COLORS['title'], width=3)
        
        # 正文
        body_font = self._get_font(38)
        body_text = body[:120] if len(body) > 120 else body
        body_lines = self._text_to_lines(body_text, 32)
        for i, line in enumerate(body_lines):
            bbox = draw.textbbox((0, 0), line, font=body_font)
            tw = bbox[2] - bbox[0]
            x = (w-tw)//2
            y = 420 + i*52
            draw.text((x+1, y+1), line, fill=(200, 200, 200), font=body_font)
            draw.text((x, y), line, fill=self.COLORS['body'], font=body_font)
        
        # 可选额外信息
        if extra:
            extra_font = self._get_font(26)
            draw.text((50, h-160), extra, fill=self.COLORS['accent'], font=extra_font)
        
        # CTA
        cta_font = self._get_font(32)
        cta_text = cta[:45] if len(cta) > 45 else cta
        bbox = draw.textbbox((0, 0), cta_text, font=cta_font)
        tw = bbox[2] - bbox[0]
        x = (w-tw)//2
        y = h - 320
        draw.rectangle([x-20, y-10, x+tw+20, y+55], 
                      fill=(20, 40, 80, 180), outline=self.COLORS['cta'], width=2)
        draw.text((x, y), "→ " + cta_text, fill=self.COLORS['cta'], font=cta_font)
        
        # 底部品牌
        info_font = self._get_font(20)
        draw.text((50, h-80), f"{self.brand.get('name', '九箭新能源')} | 专业光伏获客方案", 
                  fill=self.COLORS['brand'], font=info_font)
        
        return img.convert('RGB')
    
    def synthesize_video(self, script_data, output_path=None):
        """合成视频"""
        if Image is None:
            return None
        
        temp_dir = tempfile.mkdtemp(prefix='pv_vid_')
        try:
            title = script_data.get("title", "光伏内容").replace('?', '？').replace('！', '！')
            body = script_data.get("body", "")
            cta = script_data.get("cta", "关注获取更多")
            province = script_data.get("geo_primary_province", "全国")
            direction = script_data.get("direction", "news")
            
            # 获取背景图
            bg_path = self._get_bg_image(direction)
            
            # 帧1：标题+正文
            frame = self._render_slide(title, body[:100], cta, bg_path, f"📍 {province}")
            fp = os.path.join(temp_dir, "frame_0000.png")
            frame.save(fp, 'PNG')
            frame_paths = [fp]
            
            # 帧2-4：正文分点
            body_lines = self._text_to_lines(body, 28)
            for i, line in enumerate(body_lines[:3]):
                frame = self._render_slide("", line, cta, bg_path, f"📍 {province}")
                fp = os.path.join(temp_dir, f"frame_{i+1:04d}.png")
                frame.save(fp, 'PNG')
                frame_paths.append(fp)
            
            # 帧5：CTA收尾
            frame = self._render_slide("立即咨询", "", cta, bg_path, f"📍 {province}")
            fp = os.path.join(temp_dir, f"frame_{len(frame_paths):04d}.png")
            frame.save(fp, 'PNG')
            frame_paths.append(fp)
            
            if not frame_paths:
                return None
            
            # TTS
            if not _has_edge_tts:
                return None
            tid = script_data.get("tracking_id", "pv_" + datetime.now().strftime("%Y%m%d_%H%M"))
            audio_path = os.path.join(temp_dir, tid + ".mp3")
            full_text = script_data.get("full_script", body)
            for voice in ["zh-CN-YunxiNeural", "zh-CN-XiaoxiaoNeural", "zh-CN-XiaoyiNeural"]:
                try:
                    communicate = edge_tts.Communicate(full_text, voice)
                    import asyncio
                    asyncio.run(communicate.save(audio_path))
                    if os.path.exists(audio_path) and os.path.getsize(audio_path) > 1000:
                        break
                except Exception:
                    continue
            else:
                return None
            
            # 音频时长
            r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                              "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
                             capture_output=True, text=True, timeout=10)
            audio_dur = float(r.stdout.strip()) if r.returncode == 0 else 10
            
            fps = self.fps
            seg_frames = max(int(audio_dur / len(frame_paths) * fps), 2)
            
            # zoompan
            seg_paths = []
            for i, fp in enumerate(frame_paths):
                seg_out = os.path.join(temp_dir, f"seg_{i:04d}.mp4")
                zoom_end = 1.03
                zoom_step = (zoom_end - 1.0) / max(seg_frames, 1)
                filter_str = (
                    f"[0:v]zoompan=z='min(zoom+{zoom_step:.4f},{zoom_end})':"
                    f"d={seg_frames}:x=iw/2-(iw/zoom/2):y=ih/2-(ih/zoom/2):"
                    f"s={self.width}x{self.height}[v]"
                )
                cmd = [
                    "ffmpeg", "-y", "-loop", "1", "-i", fp,
                    "-filter_complex", filter_str,
                    "-map", "[v]",
                    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22",
                    "-pix_fmt", "yuv420p",
                    "-t", str(seg_frames / fps),
                    seg_out
                ]
                r = subprocess.run(cmd, capture_output=True, timeout=30)
                if r.returncode == 0 and os.path.exists(seg_out):
                    seg_paths.append(seg_out)
            
            if not seg_paths:
                return None
            
            # concat + audio
            concat_file = os.path.join(temp_dir, "concat.txt")
            with open(concat_file, "w", encoding="utf-8") as f:
                for sp in seg_paths:
                    f.write(f"file '{sp}'\n")
            
            concat_out = os.path.join(temp_dir, "concat.mp4")
            subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                          "-i", concat_file, "-c", "copy", concat_out],
                         capture_output=True, timeout=60)
            
            final_out = output_path or os.path.join(self.output_dir, tid + ".mp4")
            subprocess.run(["ffmpeg", "-y",
                           "-i", concat_out, "-i", audio_path,
                           "-c:v", "copy", "-c:a", "aac", "-shortest", final_out],
                         capture_output=True, timeout=60)
            
            if os.path.exists(final_out):
                return final_out
            return None
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    composer = PVVideoComposer()
    test_script = {
        "title": "屋顶装光伏到底划不划算？",
        "body": "以常见的5kW-10kW屋顶光伏为例，结合当前组件价格和上网电价，真实算一笔账：前期投入约1.5万，每年发电约5000度，回本周期3-4年，25年寿命期总收益可达8万+",
        "cta": "点关注私信我，免费帮你测算当地政策",
        "full_script": "屋顶装光伏到底划不划算？以常见的5kW-10kW屋顶光伏为例，结合当前组件价格和上网电价，真实算一笔账：前期投入约1.5万，每年发电约5000度，回本周期3-4年，25年寿命期总收益可达8万+。",
        "tracking_id": "PV_VIDEO_V5_TEST",
        "direction": "benefit",
        "geo_primary_province": "重庆",
    }
    result = composer.synthesize_video(test_script)
    if result:
        print("Video created: " + result)
        sz = os.path.getsize(result) // 1024
        print("Size: " + str(sz) + " KB")
    else:
        print("Video creation failed")
