# -*- coding: utf-8 -*-
"""
抖音内容提取工具 v3.0
=========================
按内容类型自动选择最优提取方案

类型检测:
  - 多图帖子 (images>=2) → easyocr 逐图识别
  - 长视频 (duration>=60s) → Whisper 音频转写
  - 短/图文视频 → desc 文案为主

用法:
    python scripts/douyin_extractor.py https://v.douyin.com/xxxxx/
"""
import sys, json, re, os, subprocess, urllib.request
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import warnings; warnings.filterwarnings('ignore')

try:
    import requests
except ImportError:
    print("需要: pip install requests")
    sys.exit(1)

try:
    import easyocr
    from PIL import Image
    import numpy as np
    _HAS_EASYOCR = True
except ImportError:
    _HAS_EASYOCR = False

WORKSPACE = Path(r"C:\Users\Administrator\.openclaw\workspace\workspace-investment")
OUT_DIR = WORKSPACE / "out_data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

_ocr_reader = None
def _get_reader():
    global _ocr_reader
    if _ocr_reader is None and _HAS_EASYOCR:
        _ocr_reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
    return _ocr_reader

def _parse_video_info_res(html, url):
    """从SSR HTML中解析videoInfoRes JSON"""
    vir_start = html.find('"videoInfoRes"')
    if vir_start < 0:
        desc = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]*)"', html)
        if desc:
            return {"desc": desc.group(1), "source": "meta", "url": url}
        return {"error": "未找到视频数据", "url": url}
    
    item_list_pos = html.find('"item_list"', vir_start)
    if item_list_pos < 0:
        return {"error": "未找到item_list", "url": url}
    
    brace_start = html.find('[', item_list_pos)
    if brace_start < 0:
        return {"error": "未找到数组起始", "url": url}
    
    depth = 0; in_str = False; esc = False; end = brace_start
    for i in range(brace_start, len(html)):
        if esc: esc = False; continue
        if html[i] == '\\': esc = True; continue
        if html[i] == '"': in_str = not in_str; continue
        if in_str: continue
        if html[i] == '[': depth += 1
        elif html[i] == ']': depth -= 1
        if depth == 0: end = i + 1; break
    
    items = json.loads(html[brace_start:end])
    if not items:
        return {"error": "item_list为空", "url": url}
    
    return items[0]


def extract_douyin(url, transcribe=True, ocr=True):
    """
    提取抖音内容，自动按类型选择方案
    
    Args:
        url: 抖音链接
        transcribe: 是否尝试音频转写（长视频）
        ocr: 是否尝试OCR（多图帖子）
    
    Returns:
        dict: 包含类型标记、文案、作者、统计、转写/OCR文字
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) '
                      'AppleWebKit/605.1.15 (KHTML, like Gecko) '
                      'Version/16.0 Mobile/15E148 Safari/604.1',
    }
    
    r = requests.get(url, headers=headers, allow_redirects=True, timeout=15, verify=False)
    item = _parse_video_info_res(r.text, url)
    
    if "error" in item:
        return item
    
    # 基本信息
    result = {
        "type": "unknown",
        "desc": item.get('desc', ''),
        "author": {
            "nickname": item.get('author', {}).get('nickname', ''),
            "signature": item.get('author', {}).get('signature', ''),
        },
        "statistics": {
            "digg_count": item.get('statistics', {}).get('digg_count', 0),
            "comment_count": item.get('statistics', {}).get('comment_count', 0),
            "share_count": item.get('statistics', {}).get('share_count', 0),
            "collect_count": item.get('statistics', {}).get('collect_count', 0),
        },
        "video": {
            "duration": item.get('video', {}).get('duration', 0),
        },
        "tags": [],
        "music": {},
        "images_count": 0,
        "content": None,   # 最终提取的完整内容（音频转写或OCR文字）
        "content_type": None,  # "transcript" | "ocr" | "desc_only"
        "url": r.url,
    }
    
    # 话题标签
    text_extra = item.get('text_extra', [])
    if text_extra:
        result["tags"] = [te.get('hashtag_name', '') for te in text_extra if te.get('hashtag_name')]
    
    # 音乐
    music = item.get('music', {})
    if music:
        result["music"] = {"title": music.get('title', ''), "author": music.get('author', '')}
    
    # 检测内容类型并提取
    images = item.get('images') or []
    result["images_count"] = len(images)
    
    duration = item.get('video', {}).get('duration', 0)
    
    # === 方案1: 多图帖子 → OCR ===
    if len(images) >= 2 and ocr:
        result["type"] = "image_post"
        ocr_text = _ocr_images(images)
        if ocr_text:
            result["content"] = ocr_text
            result["content_type"] = "ocr"
            return result
    
    # === 方案2: 长视频 → Whisper音频转写 ===
    if duration >= 60000 and transcribe:
        result["type"] = "long_video"
        video = item.get('video', {})
        play_addr = video.get('play_addr', {})
        url_list = play_addr.get('url_list', [])
        if url_list:
            transcript = _transcribe_audio(url_list[0], duration)
            if transcript:
                result["content"] = transcript
                result["content_type"] = "transcript"
                return result
        result["content_type"] = "desc_only"
        return result
    
    # === 方案3: 短视频/封面 → desc文案 ===
    if duration > 0:
        result["type"] = "short_video"
    else:
        result["type"] = "cover"
    result["content_type"] = "desc_only"
    
    # 单张封面图也尝试OCR（可能有文字信息）
    if len(images) == 1 and ocr:
        ocr_text = _ocr_images(images)
        if ocr_text:
            result["content"] = ocr_text
            result["content_type"] = "ocr"
    
    return result


def _transcribe_audio(video_url, duration_ms):
    """方案2: Whisper音频转写（时长>60秒）"""
    video_url_clean = video_url.replace("playwm/", "play/")
    audio_path = str(OUT_DIR / "douyin_audio.mp3")
    txt_path = audio_path.replace('.mp3', '.txt')
    
    cmd = f'ffmpeg -y -i "{video_url_clean}" -vn -acodec libmp3lame -ab 128k -ar 16000 "{audio_path}" 2>nul'
    result = subprocess.run(cmd, shell=True, timeout=180)
    if result.returncode != 0:
        cmd = f'ffmpeg -y -i "{video_url}" -vn -acodec libmp3lame -ab 128k -ar 16000 "{audio_path}" 2>nul'
        result = subprocess.run(cmd, shell=True, timeout=180)
        if result.returncode != 0:
            return None
    
    timeout = 1800 if duration_ms > 1200000 else 900  # 20分钟以上给30分钟
    cmd = f'whisper "{audio_path}" --model tiny --language Chinese --output_format txt --output_dir "{OUT_DIR}" 2>nul'
    result = subprocess.run(cmd, shell=True, timeout=timeout)
    
    if os.path.exists(txt_path):
        with open(txt_path, 'r', encoding='utf-8') as f:
            text = f.read().strip()
        try: os.remove(audio_path); os.remove(txt_path)
        except: pass
        return text
    
    try: os.remove(audio_path)
    except: pass
    return None


def _ocr_images(images):
    """方案1: easyocr图片文字识别（多图帖子）"""
    reader = _get_reader()
    if not reader:
        return None
    
    all_text = []
    for i, img in enumerate(images):
        url_list = img.get('url_list', [])
        if not url_list:
            continue
        img_url = url_list[-1]  # 最高分辨率
        
        img_path = str(OUT_DIR / f"douyin_img_{i}.jpg")
        try:
            req = urllib.request.Request(img_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.douyin.com/'
            })
            r = urllib.request.urlopen(req, timeout=15)
            with open(img_path, 'wb') as f: f.write(r.read())
            
            img_pil = Image.open(img_path)
            img_np = np.array(img_pil)
            result = reader.readtext(img_np)
            text = "\n".join([item[1] for item in result])
            if text.strip():
                all_text.append(f"--- 图片{i+1} ---\n{text}")
        except Exception as e:
            all_text.append(f"--- 图片{i+1} ---\n[OCR失败: {e}]")
        finally:
            try: os.remove(img_path)
            except: pass
    
    return "\n\n".join(all_text) if all_text else None


def format_output(data):
    """格式化输出"""
    if "error" in data:
        return f"❌ 错误: {data['error']}"
    
    lines = []
    lines.append("=" * 56)
    
    # 类型标记
    type_labels = {
        "long_video": "🎬 长视频",
        "short_video": "🎬 短视频",
        "image_post": "🖼️ 图文帖子",
        "cover": "🖼️ 封面图",
    }
    lines.append(f"类型: {type_labels.get(data.get('type', ''), data.get('type', '未知'))}")
    
    lines.append(f"\n📝 文案: {data['desc']}")
    
    author = data.get('author', {})
    lines.append(f"👤 {author.get('nickname', 'N/A')} | {author.get('signature', '')}")
    
    stat = data.get('statistics', {})
    lines.append(f"📊 👍{stat.get('digg_count')} 💬{stat.get('comment_count')} 🔄{stat.get('share_count')} ⭐{stat.get('collect_count')}")
    
    video = data.get('video', {})
    if video.get('duration'):
        dur = video['duration']
        lines.append(f"⏱️ {dur//60000}分{dur%60000//1000}秒" if dur >= 60000 else f"⏱️ {dur//1000}秒")
    
    if data.get('images_count', 0) >= 2:
        lines.append(f"📸 {data['images_count']}张图片")
    
    tags = data.get('tags', [])
    if tags:
        lines.append(f"🏷️ {' '.join(['#'+t for t in tags])}")
    
    content = data.get('content')
    content_type = data.get('content_type')
    if content:
        if content_type == "transcript":
            lines.append(f"\n🎤 音频转写 ({len(content)}字):")
        elif content_type == "ocr":
            lines.append(f"\n🔍 OCR识别 ({len(content)}字):")
        lines.append(content[:600] + ("..." if len(content) > 600 else ""))
    else:
        lines.append("\n📄 仅文案（无额外内容可提取）")
    
    lines.append("\n" + "=" * 56)
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python scripts/douyin_extractor.py <抖音链接>")
        sys.exit(1)
    
    data = extract_douyin(sys.argv[1])
    print(format_output(data))