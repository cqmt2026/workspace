# -*- coding: utf-8 -*-
"""
抖音视频内容获取管线
====================
提供从抖音链接到结构化内容的完整获取能力

用法:
    from douyin_pipeline import DouyinContentPipeline
    
    pipeline = DouyinContentPipeline()
    result = pipeline.run("https://v.douyin.com/xxx/")
"""

import os
import sys
import json
import re
import subprocess
import requests
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')


class DouyinContentPipeline:
    """抖音视频内容获取管线"""
    
    def __init__(self, cookies_file=None, output_dir=None):
        """
        初始化管线
        
        Args:
            cookies_file: Cookies文件路径（默认自动检测）
            output_dir: 输出目录（默认workspace-tmp）
        """
        # 默认路径
        home = os.environ.get('USERPROFILE', r'C:\Users\Administrator')
        self.default_cookies = os.path.join(
            home, '.openclaw', 'workspace', 'workspace-math', 'L3-音频', 'douyin_cookies.json'
        )
        self.default_output = os.path.join(home, '.openclaw', 'workspace-tmp')
        
        self.cookies_file = cookies_file or self.default_cookies
        self.output_dir = output_dir or self.default_output
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 加载Cookies
        self.cookies = self._load_cookies()
        
        #  headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.douyin.com/',
        }
    
    def _load_cookies(self):
        """加载Cookies"""
        if not os.path.exists(self.cookies_file):
            print(f"警告: Cookies文件不存在: {self.cookies_file}")
            return {}
        
        with open(self.cookies_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def run(self, douyin_url, include_transcript=True, include_summary=True, include_poster=False):
        """
        执行完整流程
        
        Args:
            douyin_url: 抖音分享链接
            include_transcript: 是否生成转写
            include_summary: 是否生成摘要
            include_poster: 是否生成海报
            
        Returns:
            dict: 包含所有提取结果的字典
        """
        print("="*60)
        print("抖音视频内容获取管线")
        print("="*60)
        
        result = {
            'success': False,
            'url': douyin_url,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Step 1: 提取video_id
            print("\n[Step 1] 提取视频ID...")
            video_id = self._extract_video_id(douyin_url)
            if not video_id:
                result['error'] = '无法提取视频ID'
                return result
            result['video_id'] = video_id
            print(f"  ✓ 视频ID: {video_id}")
            
            # Step 2: 获取视频元数据
            print("\n[Step 2] 获取视频元数据...")
            meta = self._fetch_video_meta(video_id)
            if not meta.get('success'):
                result['error'] = meta.get('error', '获取元数据失败')
                return result
            result.update(meta)
            print(f"  ✓ 标题: {meta.get('title', '未知')[:50]}...")
            print(f"  ✓ 作者: {meta.get('author', {}).get('nickname', '未知')}")
            
            # Step 3: 下载视频并提取音频
            if include_transcript:
                print("\n[Step 3] 下载视频并提取音频...")
                audio_file = self._download_and_extract_audio(video_id, meta)
                if not audio_file:
                    print("  ⚠ 音频提取失败，跳过转写")
                    result['transcript'] = None
                else:
                    result['audio_file'] = audio_file
                    
                    # Step 4: 语音转写（先试音频，失败则降级到浏览器读文案）
                    print("\n[Step 4] 语音转写...")
                    transcript = self._transcribe_audio(audio_file)
                    if not transcript:
                        print("  ⚠ 音频转写失败，尝试浏览器降级方案...")
                        transcript = self._browser_fallback(video_id)
                    result['transcript_raw'] = transcript
                    
                    # Step 5: ASR修正
                    print("\n[Step 5] ASR修正...")
                    corrected = self._correct_asr(transcript, meta.get('title', ''), meta.get('tags', []))
                    result['transcript_corrected'] = corrected
            
            # Step 6: 内容摘要
            if include_summary and result.get('transcript_corrected'):
                print("\n[Step 6] 内容摘要...")
                summary = self._summarize_content(result['transcript_corrected'])
                result['summary'] = summary
            
            # Step 7: 生成海报
            # 如果没有转写文本但有元数据，至少生成纯信息海报
            include_poster = include_poster or (result.get('title') and not result.get('transcript_raw'))
            if include_poster:
                print("\n[Step 7] 生成海报...")
                poster_path = self._generate_poster(result)
                result['poster_path'] = poster_path
            
            result['success'] = True
            print("\n" + "="*60)
            print("✓ 处理完成")
            print("="*60)
            
        except Exception as e:
            result['error'] = str(e)
            print(f"\n✗ 错误: {e}")
        
        return result
    
    def _extract_video_id(self, url):
        """从URL提取video_id"""
        # 短链解析
        if 'v.douyin.com' in url:
            # 尝试直接解析
            match = re.search(r'v\.douyin\.com/([^/?]+)', url)
            if match:
                short_code = match.group(1)
                # 短链需要重定向获取真实ID
                try:
                    r = requests.head(url, headers=self.headers, allow_redirects=True, timeout=10)
                    final_url = r.url
                    match = re.search(r'/video/(\d+)', final_url)
                    if match:
                        return match.group(1)
                except:
                    pass
            return None
        
        # 长链解析
        match = re.search(r'/video/(\d+)', url)
        return match.group(1) if match else None
    
    def _fetch_video_meta(self, video_id):
        """获取视频元数据"""
        api_url = f'https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id={video_id}&aid=6383'
        
        try:
            r = requests.get(api_url, headers=self.headers, cookies=self.cookies, timeout=15)
            data = r.json()
            
            if 'aweme_detail' not in data:
                return {'success': False, 'error': 'API返回异常'}
            
            aweme = data['aweme_detail']
            
            # 提取基本信息
            author = aweme.get('author', {})
            stats = aweme.get('statistics', {})
            text_extra = aweme.get('text_extra', [])
            tags = [t.get('hashtag_name', '') for t in text_extra if t.get('hashtag_name')]
            
            return {
                'success': True,
                'title': aweme.get('desc', ''),
                'duration': aweme.get('duration', 0) / 1000,
                'author': {
                    'nickname': author.get('nickname', ''),
                    'uid': author.get('uid', ''),
                    'followers': author.get('follower_count', 0),
                    'signature': author.get('signature', '')
                },
                'statistics': {
                    'likes': stats.get('digg_count', 0),
                    'comments': stats.get('comment_count', 0),
                    'shares': stats.get('share_count', 0),
                    'collects': stats.get('collect_count', 0)
                },
                'tags': tags,
                'create_time': aweme.get('create_time', 0)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _download_and_extract_audio(self, video_id, meta):
        """下载视频并提取音频"""
        # 获取播放地址
        video = meta.get('_raw', {}).get('video', {})
        play_addr = video.get('play_addr', {})
        url_list = play_addr.get('url_list', [])
        
        if not url_list:
            # 重新获取
            api_url = f'https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id={video_id}&aid=6383'
            r = requests.get(api_url, headers=self.headers, cookies=self.cookies, timeout=15)
            data = r.json()
            video = data['aweme_detail'].get('video', {})
            play_addr = video.get('play_addr', {})
            url_list = play_addr.get('url_list', [])
        
        if not url_list:
            return None
        
        video_url = url_list[0]
        video_file = os.path.join(self.output_dir, f'douyin_{video_id}.mp4')
        audio_file = os.path.join(self.output_dir, f'douyin_{video_id}.wav')
        
        # 下载视频
        print(f"  下载视频: {video_url[:60]}...")
        try:
            r = requests.get(video_url, headers=self.headers, cookies=self.cookies, timeout=120, stream=True)
            if r.status_code == 200:
                with open(video_file, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"  ✓ 下载完成: {os.path.getsize(video_file)/1024/1024:.1f} MB")
            else:
                print(f"  ✗ 下载失败: HTTP {r.status_code}")
                return None
        except Exception as e:
            print(f"  ✗ 下载错误: {e}")
            return None
        
        # 提取音频
        print(f"  提取音频...")
        try:
            cmd = [
                'ffmpeg', '-i', video_file,
                '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
                audio_file, '-y'
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=60)
            if os.path.exists(audio_file):
                print(f"  ✓ 音频提取完成")
                return audio_file
            else:
                print(f"  ✗ 音频提取失败")
                return None
        except Exception as e:
            print(f"  ✗ FFmpeg错误: {e}")
            return None
    
    def _transcribe_audio(self, audio_file):
        """使用Whisper转写音频（优先tiny，失败降级到base）"""
        for model_name in ['tiny', 'base']:
            try:
                import whisper
                print(f"  加载Whisper {model_name}模型...")
                model = whisper.load_model(model_name)
                print(f"  开始转写...")
                result = model.transcribe(audio_file, language='zh')
                print(f"  ✓ 转写完成: {len(result['text'])} 字符")
                return result['text']
            except Exception as e:
                print(f"  ✗ {model_name}转写错误: {e}")
                if model_name == 'tiny':
                    print("  → 自动降级到base模型")
                    continue
                return None
        return None
    
    def _correct_asr(self, text, title, tags):
        """修正ASR错误 - 使用统一修正器"""
        if not text:
            return None
        
        # 导入统一修正器
        try:
            sys.path.insert(0, os.path.dirname(__file__))
            from correct_asr import correct_asr as rule_correct
            return rule_correct(text, context=title)
        except ImportError:
            # 回退到内联修正
            return self._inline_correct_asr(text, title, tags)
    
    def _summarize_content(self, transcript):
        """生成内容摘要"""
        # 简化版：提取关键段落
        if not transcript:
            return None
        
        # 按句号分段
        sentences = re.split(r'[。！？]', transcript)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # 提取关键句（包含关键词）
        keywords = ['核心', '关键', '第一', '第二', '第三', '总结', '判断', '标准']
        key_sentences = []
        for s in sentences:
            if any(k in s for k in keywords):
                key_sentences.append(s)
        
        # 如果关键句太少，取前5句
        if len(key_sentences) < 3:
            key_sentences = sentences[:5]
        
        summary = '\n'.join(key_sentences[:10])
        return summary
    
    def _browser_fallback(self, video_id):
        """降级方案：通过浏览器读取视频页面文案"""
        try:
            from playwright.sync_api import sync_playwright
            url = f"https://www.douyin.com/video/{video_id}"
            print(f"  打开浏览器: {url}")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(viewport={'width': 1280, 'height': 800})
                page.goto(url, wait_until='networkidle', timeout=30000)
                page.wait_for_timeout(3000)
                # 提取页面文本
                text = page.inner_text('body')
                browser.close()
                # 清理文本
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                # 过滤掉导航/按钮等UI文字，保留主要内容
                content_lines = []
                for line in lines:
                    if len(line) > 10 and not any(x in line for x in ['关注', '首页', '发现', '商城', '我的']):
                        content_lines.append(line)
                fallback_text = '\n'.join(content_lines[:50])
                print(f"  ✓ 浏览器降级成功: {len(fallback_text)} 字符")
                return fallback_text
        except Exception as e:
            print(f"  ✗ 浏览器降级也失败: {e}")
            return None

    def _generate_poster(self, result):
        """生成海报"""
        try:
            from playwright.sync_api import sync_playwright
            
            html_content = self._build_poster_html(result)
            html_file = os.path.join(self.output_dir, 'poster_temp.html')
            png_file = os.path.join(self.output_dir, f'poster_{result["video_id"]}.png')
            
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(viewport={'width': 1000, 'height': 1600})
                page.goto(f'file:///{html_file.replace(chr(92), "/")}', wait_until='networkidle')
                page.wait_for_timeout(2000)
                page.screenshot(path=png_file, full_page=True)
                browser.close()
            
            os.remove(html_file)
            print(f"  ✓ 海报已生成: {png_file}")
            return png_file
        except Exception as e:
            print(f"  ✗ 海报生成失败: {e}")
            return None
    
    def _build_poster_html(self, result):
        """构建海报HTML"""
        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>视频内容摘要</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 40px;
        }}
        .card {{
            background: white;
            border-radius: 20px;
            padding: 50px;
            max-width: 800px;
            width: 100%;
            box-shadow: 0 30px 80px rgba(0,0,0,0.3);
        }}
        h1 {{
            font-size: 36px;
            color: #2d3436;
            margin-bottom: 30px;
            text-align: center;
        }}
        .meta {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}
        .meta-item {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 12px;
        }}
        .meta-label {{
            font-size: 14px;
            color: #636e72;
            margin-bottom: 8px;
        }}
        .meta-value {{
            font-size: 20px;
            font-weight: 700;
            color: #2d3436;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 15px;
            padding-left: 15px;
            border-left: 4px solid #667eea;
        }}
        .content {{
            font-size: 16px;
            line-height: 1.8;
            color: #2d3436;
            text-align: justify;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #dfe6e9;
            text-align: center;
            font-size: 14px;
            color: #b2bec3;
        }}
    </style>
</head>
<body>
    <div class="card">
        <h1>📹 抖音视频内容摘要</h1>
        
        <div class="meta">
            <div class="meta-item">
                <div class="meta-label">视频标题</div>
                <div class="meta-value">{result.get('title', '未知')}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">作者</div>
                <div class="meta-value">{result.get('author', {}).get('nickname', '未知')}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">点赞数</div>
                <div class="meta-value">{result.get('statistics', {}).get('likes', 0):,}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">时长</div>
                <div class="meta-value">{result.get('duration', 0):.0f}秒</div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">核心内容</div>
            <div class="content">
                {((result.get('summary') or result.get('transcript_corrected') or result.get('transcript_raw') or '暂无内容')[:1000])}...
            </div>
        </div>
        
        <div class="footer">
            生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')} | 由OpenClaw系统自动生成
        </div>
    </div>
</body>
</html>'''


# 便捷函数
def get_douyin_content(url, **kwargs):
    """便捷函数：获取抖音视频内容"""
    pipeline = DouyinContentPipeline()
    return pipeline.run(url, **kwargs)


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("用法: python douyin_pipeline.py <抖音链接>")
        sys.exit(1)
    
    url = sys.argv[1]
    result = get_douyin_content(url)
    
    if result['success']:
        print("\n" + "="*60)
        print("处理成功!")
        print("="*60)
        print(f"标题: {result['title']}")
        print(f"作者: {result['author']['nickname']}")
        print(f"点赞: {result['statistics']['likes']}")
        print(f"\n转写文本（前200字符）:")
        print(result.get('transcript_corrected', result.get('transcript_raw', ''))[:200])
    else:
        print(f"\n处理失败: {result.get('error', '未知错误')}")
