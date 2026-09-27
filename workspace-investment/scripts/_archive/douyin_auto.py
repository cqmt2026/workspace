# -*- coding: utf-8 -*-
"""
抖音视频完整内容提取器 v2.0
============================
新增：音频转文字（Whisper）功能
- 如果视频时长>60秒且有音频，自动用Whisper转写
- 转写结果合并到归档笔记

用法:
    python scripts/douyin_auto.py https://v.douyin.com/xxxxx/
    
依赖:
    - openai-whisper (pip install openai-whisper)
    - ffmpeg (需在PATH中)
"""
import io
import sys, os, json, re, subprocess
from datetime import datetime, date
from pathlib import Path
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

WORKSPACE = Path(r"C:\Users\Administrator\.openclaw\workspace\workspace-investment")
OBSIDIAN_VAULT = Path(r"C:\Users\Administrator\Obsidian\Jarvis")
OUT_DIR = WORKSPACE / "out_data"

# 导入抖音提取器
sys.path.insert(0, str(WORKSPACE / "scripts"))
from douyin_extractor import extract_douyin_video, format_output


def download_and_transcribe(video_url, duration_ms):
    """
    下载视频音频并用Whisper转写文字
    
    Args:
        video_url: 视频播放地址
        duration_ms: 视频时长(毫秒)
        
    Returns:
        str: 转写文本，失败返回None
    """
    # 小于60秒的视频不转写（可能内容太少）
    if duration_ms < 60000:
        print("  ⏱️ 视频较短(<60s)，跳过音频转写")
        return None
    
    # 去掉水印
    video_url_clean = video_url.replace("playwm/", "play/")
    
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    audio_path = str(OUT_DIR / "douyin_audio.mp3")
    txt_path = audio_path.replace('.mp3', '.txt')
    
    # 1. 下载音频
    print("  📥 下载音频...")
    cmd = f'ffmpeg -y -i "{video_url_clean}" -vn -acodec libmp3lame -ab 128k -ar 16000 "{audio_path}" 2>nul'
    result = subprocess.run(cmd, shell=True, timeout=120)
    if result.returncode != 0:
        # 尝试带水印版本
        cmd = f'ffmpeg -y -i "{video_url}" -vn -acodec libmp3lame -ab 128k -ar 16000 "{audio_path}" 2>nul'
        result = subprocess.run(cmd, shell=True, timeout=120)
        if result.returncode != 0:
            print("  ❌ ffmpeg下载失败")
            return None
    
    audio_size = os.path.getsize(audio_path)
    print(f"  ✅ 下载完成: {audio_size/1024:.0f}KB")
    
    # 2. Whisper转写
    print("  🎤 Whisper转写 (tiny模型)...")
    cmd = f'whisper "{audio_path}" --model tiny --language Chinese --output_format txt --output_dir "{OUT_DIR}" 2>nul'
    result = subprocess.run(cmd, shell=True, timeout=600)
    
    # 3. 读取结果
    if os.path.exists(txt_path):
        with open(txt_path, 'r', encoding='utf-8') as f:
            text = f.read().strip()
        # 清理临时文件
        try:
            os.remove(audio_path)
            os.remove(txt_path)
        except:
            pass
        print(f"  ✅ 转写完成: {len(text)}字")
        return text
    else:
        print("  ❌ 转写失败")
        # 清理音频
        try:
            os.remove(audio_path)
        except:
            pass
        return None


def extract_video_urls(html):
    """从SSR HTML中提取视频下载地址"""
    # 找videoInfoRes中的play_addr
    play_match = re.search(r'"play_addr"\s*:\s*\{[^}]*"url_list"\s*:\s*\[([^\]]+)\]', html)
    if play_match:
        urls = re.findall(r'"([^"]+)"', play_match.group(1))
        if urls:
            return urls[0]
    return None


def extract_video_duration(html):
    """从SSR HTML中提取视频时长"""
    dur_match = re.search(r'"duration"\s*:\s*(\d+)', html)
    if dur_match:
        return int(dur_match.group(1))
    return 0


def extract_full_content(url):
    """提取视频完整内容（文案+音频转写）"""
    print(f"🔍 正在提取: {url}")
    
    # 1. 获取SSR HTML
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'}
    req = urllib.request.Request(url, headers=headers)
    r = urllib.request.urlopen(req, timeout=15)
    html = r.read().decode('utf-8', errors='replace')
    
    # 2. 提取基本信息
    data = extract_douyin_video(url)
    
    if "error" in data:
        print(f"❌ 提取失败: {data['error']}")
        return data
    
    print(format_output(data))
    
    # 3. 提取视频URL
    video_url = extract_video_urls(html)
    duration = data.get('video', {}).get('duration', 0)
    
    # 4. 音频转写
    transcript = None
    if video_url and duration > 0:
        print(f"\n🎤 尝试音频转写 (时长: {duration/1000:.0f}秒)...")
        transcript = download_and_transcribe(video_url, duration)
    else:
        print("  ⏭️ 未找到视频下载地址或时长")
    
    data['transcript'] = transcript
    return data


def classify_content(desc, tags):
    """根据文案内容智能分类"""
    desc_lower = desc.lower()
    
    if any(k in desc_lower for k in ['论文', '模型', '算法', '研究', '深度学习', '机器学习', '强化学习', 
                                       'transformer', 'cnn', 'lstm', '回测', '策略']):
        return '策略笔记', '论文启发'
    
    if any(k in desc for k in ['概念股', '产业链', '板块', '行业', '龙头']):
        return '行业研究', '概念股'
    
    if any(k in desc for k in ['方法', '技巧', '策略', '交易', '买入', '卖出', '买点', '卖点',
                                 '止盈', '止损', '仓位', '低吸', '追涨']):
        return '策略笔记', '交易心法'
    
    if any(k in desc for k in ['主力', '资金', '筹码', '成本', '量价']):
        return '策略笔记', '资金分析'
    
    for t in tags:
        t_lower = t.lower()
        if any(k in t_lower for k in ['量化', '策略', '交易']):
            return '策略笔记', '量化'
    
    return '策略笔记', '通用'


def generate_filename(desc, category, subcategory):
    """生成文件名"""
    words = re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]+', desc)
    keywords = [w for w in words if len(w) >= 2 and w not in ['一个', '就是', '什么', '可以', '这个', '那个', '我们', '你们', '他们']]
    name = '_'.join(keywords[:2]) if keywords else '未分类'
    if len(name) > 20:
        name = name[:20]
    today = date.today().strftime('%Y-%m-%d')
    return f"{today}_{name}.md"


def archive_to_obsidian(data):
    """归档到Obsidian知识库"""
    desc = data.get('desc', '')
    tags_list = data.get('tags', [])
    author = data.get('author', {})
    nickname = author.get('nickname', '未知')
    transcript = data.get('transcript', '')
    stat = data.get('statistics', {})
    video = data.get('video', {})
    
    category, subcategory = classify_content(desc, tags_list)
    
    if category == '行业研究':
        target_dir = OBSIDIAN_VAULT / '03-知识' / '投资行业研究'
    else:
        target_dir = OBSIDIAN_VAULT / '03-项目' / '贾维斯系统' / '策略笔记'
    
    target_dir.mkdir(parents=True, exist_ok=True)
    
    filename = generate_filename(desc, category, subcategory)
    filepath = target_dir / filename
    
    all_tags = [subcategory, '抖音归档']
    if transcript:
        all_tags.append('音频转写')
    for t in tags_list:
        if t:
            all_tags.append(t)
    
    md_parts = [
        "---",
        f"tags: [{', '.join(all_tags)}]",
        f"date: {date.today().isoformat()}",
        f"source: 抖音@{nickname}",
        "status: 待验证",
        "---",
        "",
        f"# {desc[:60] if len(desc) > 60 else desc}",
        "",
        f"> 来源：抖音@{nickname}",
        f"> 时长: {video.get('duration',0)/1000:.0f}秒" if video.get('duration') else '> 时长: 未知',
        f"> 数据: 👍{stat.get('digg_count',0)} 💬{stat.get('comment_count',0)} 🔄{stat.get('share_count',0)} ⭐{stat.get('collect_count',0)}",
        "",
        "## 完整文案",
        "",
        f"> {desc}",
        "",
    ]
    
    # 音频转写内容
    if transcript:
        md_parts.extend([
            "## 音频转写内容",
            "",
            "> " + transcript.replace('\n', '\n> '),
            "",
        ])
    
    md_parts.extend([
        "## 作者信息",
        f"- **昵称**: {nickname}",
        f"- **签名**: {author.get('signature', '无')}",
        "",
        "## 话题标签",
        f"{' '.join(['#' + t for t in tags_list]) if tags_list else '无'}",
        "",
        "## 系统关联分析",
        "",
        "*（待主人讨论后补充）*",
        "",
        "## 待办",
        "- [ ] 主人讨论后补充分析和落地计划",
    ])
    
    md = "\n".join(md_parts)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(md)
    
    print(f"\n✅ 已归档: {filepath}")
    return filepath, category


def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/douyin_auto.py <抖音链接>")
        sys.exit(1)
    
    url = sys.argv[1]
    data = extract_full_content(url)
    
    if "error" in data:
        sys.exit(1)
    
    filepath, category = archive_to_obsidian(data)
    print(f"📂 分类: {category}")
    print(f"📄 文件: {filepath.name}")
    print("✅ 完成!")


if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == "__main__":
    main()