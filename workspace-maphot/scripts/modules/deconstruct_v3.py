# -*- coding: utf-8 -*-
"""
抖音视频拆解增强版 v3 - 集成PySceneDetect + video-analyzer核心逻辑
=================================================
在 v2 基础上增加：
1. PySceneDetect 场景切换检测 → 精确提取转场点
2. OpenCV 自适应关键帧提取（基于video-analyzer的frame.py算法）
3. 预留画面分析接口（LLM Vision分析关键帧内容）

依赖：
- whisper (已安装)
- ffmpeg (已安装)
- scenedetect (已安装)
- opencv-python (已安装)
- modules.douyin_analyzer (已有)

用法：
    from modules.deconstruct_v3 import deconstruct_video_v3
    
    # 拆解单条视频（含场景检测+转写+关键帧）
    report = deconstruct_video_v3("https://v.douyin.com/xxx/", 
                                  transcribe=True, 
                                  detect_scenes=True,
                                  analyze_frames=True)
"""

import json
import os
import logging
import re
import subprocess
import tempfile
import sys
import glob
import shutil
from datetime import datetime
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
from pathlib import Path
import base64

# 确保模块目录在路径中
_SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

logger = logging.getLogger(__name__)

# ============================================================
# 第一部分：PySceneDetect 场景检测
# ============================================================

def detect_scenes(video_path: str, threshold: float = 27.0) -> List[Dict]:
    """
    使用 PySceneDetect 检测视频场景切换点
    
    Args:
        video_path: 视频文件路径
        threshold: 内容检测阈值（越小越敏感）
        
    Returns:
        list: 场景列表，每个包含 start_time, end_time, duration
    """
    try:
        from scenedetect import detect, ContentDetector, AdaptiveDetector
        
        logger.info(f"[SCENE] 检测场景切换: {os.path.basename(video_path)} (threshold={threshold})")
        
        # 先用 ContentDetector 检测快速切
        scene_list = detect(video_path, ContentDetector(threshold=threshold))
        
        # 如果没有检测到，用 AdaptiveDetector 再试（更适合运动场景）
        if not scene_list:
            logger.info("[SCENE] ContentDetector 未检测到场景，尝试 AdaptiveDetector...")
            scene_list = detect(video_path, AdaptiveDetector())
        
        scenes = []
        for i, (start, end) in enumerate(scene_list):
            start_time = start.get_seconds()
            end_time = end.get_seconds()
            scenes.append({
                'scene_index': i + 1,
                'start_time': round(start_time, 1),
                'end_time': round(end_time, 1),
                'duration': round(end_time - start_time, 1),
                'start_timecode': start.get_timecode(),
                'end_timecode': end.get_timecode(),
            })
        
        logger.info(f"[SCENE] 检测到 {len(scenes)} 个场景")
        for s in scenes[:5]:
            logger.info(f"  场景 {s['scene_index']}: {s['start_timecode']} -> {s['end_timecode']} ({s['duration']}s)")
        
        return scenes
        
    except ImportError:
        logger.warning("[SCENE] scenedetect 未安装，跳过场景检测")
        return []
    except Exception as e:
        logger.error(f"[SCENE] 场景检测失败: {e}")
        return []


# ============================================================
# 第二部分：OpenCV 自适应关键帧提取（基于video-analyzer算法）
# ============================================================

@dataclass
class Frame:
    """关键帧数据结构"""
    index: int
    path: Path
    timestamp: float
    score: float


def extract_keyframes_adaptive(video_path: str, output_dir: str,
                               frames_per_minute: int = 10,
                               max_frames: int = 30,
                               threshold: float = 10.0) -> List[Dict]:
    """
    自适应关键帧提取（基于video-analyzer的frame.py算法）
    
    核心逻辑：
    1. 按目标帧数计算采样间隔
    2. 逐帧计算帧间差异（absdiff + mean）
    3. 差异超过阈值的帧作为候选
    4. 按差异分数排序，取前N帧
    5. 按时间顺序输出
    
    Args:
        video_path: 视频文件路径
        output_dir: 输出目录
        frames_per_minute: 每分钟目标帧数
        max_frames: 最大帧数
        threshold: 帧差异阈值
        
    Returns:
        list: 关键帧列表，每个包含 index, path, timestamp, score
    """
    try:
        import cv2
        import numpy as np
    except ImportError:
        logger.error("[FRAME] OpenCV 未安装，无法提取关键帧")
        return []
    
    os.makedirs(output_dir, exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"[FRAME] 无法打开视频: {video_path}")
        return []
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_duration = total_frames / fps if fps > 0 else 0
    
    logger.info(f"[FRAME] 视频: {fps:.1f}fps, {total_frames}帧, {video_duration:.1f}s")
    
    # 计算目标帧数
    target_frames = max(1, min(
        int((video_duration / 60) * frames_per_minute),
        total_frames,
        max_frames
    ))
    
    # 自适应采样间隔
    sample_interval = max(1, total_frames // (target_frames * 2))
    
    # 逐帧扫描，收集候选帧
    frame_candidates = []
    prev_frame = None
    frame_count = 0
    
    while frame_count < total_frames:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % sample_interval == 0:
            # 计算帧间差异
            if prev_frame is not None:
                gray1 = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
                gray2 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                diff = cv2.absdiff(gray1, gray2)
                score = float(np.mean(diff))
            else:
                score = float('inf')
            
            if score > threshold:
                frame_candidates.append((frame_count, frame, score))
            prev_frame = frame.copy()
        
        frame_count += 1
    
    cap.release()
    
    # 按分数排序，取前N帧
    selected = sorted(frame_candidates, key=lambda x: x[2], reverse=True)[:target_frames]
    
    # 按时间顺序重排
    selected = sorted(selected, key=lambda x: x[0])
    
    # 保存帧
    frames = []
    for idx, (frame_num, frame, score) in enumerate(selected):
        frame_path = os.path.join(output_dir, f"frame_{idx:04d}.jpg")
        cv2.imwrite(frame_path, frame)
        timestamp = frame_num / fps if fps > 0 else 0
        frames.append({
            'index': idx,
            'path': frame_path,
            'timestamp': round(timestamp, 1),
            'score': round(score, 1),
        })
    
    logger.info(f"[FRAME] 提取了 {len(frames)} 个关键帧 (目标: {target_frames})")
    return frames


# ============================================================
# 第三部分：关键帧画面分析（LLM Vision）
# ============================================================

def encode_image_to_base64(image_path: str) -> str:
    """将图片编码为base64"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')


def analyze_frames_with_vision(frames: List[Dict], 
                               api_key: str = None,
                               api_url: str = "https://openrouter.ai/api/v1",
                               model: str = "meta-llama/llama-3.2-11b-vision-instruct:free",
                               max_frames: int = 5) -> List[Dict]:
    """
    使用 LLM Vision API 分析关键帧画面内容
    
    通过 OpenRouter 调用 Vision 模型，逐帧分析画面内容。
    分析维度：视觉风格、主要元素、文字内容、颜色风格、动画效果
    
    Args:
        frames: 关键帧列表
        api_key: OpenRouter API Key
        api_url: API 地址
        model: Vision 模型名
        max_frames: 最大分析帧数
        
    Returns:
        list: 每帧的分析结果
    """
    if not api_key:
        logger.warning("[VISION] 未提供 API Key，跳过画面分析")
        return []
    
    analyses = []
    frames_to_analyze = frames[:max_frames]
    
    for frame in frames_to_analyze:
        try:
            import requests
            
            base64_image = encode_image_to_base64(frame['path'])
            
            prompt = f"""请描述这个视频帧的画面内容。分析维度：
1. 视觉风格（地图/动画/实拍/文字/数据图表）
2. 主要视觉元素（地图、文字、数据、人物等）
3. 画面中的文字/字幕内容
4. 颜色风格（深色/亮色/冷暖色调）
5. 动画/转场效果（如果有）
6. 制作难度（简单/中等/复杂）

这是视频第 {frame['timestamp']} 秒的帧。"""

            data = {
                "model": model,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }],
                "max_tokens": 200,
                "temperature": 0.1
            }
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{api_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            description = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            analyses.append({
                'frame_index': frame['index'],
                'timestamp': frame['timestamp'],
                'description': description,
                'success': True
            })
            
            logger.info(f"[VISION] 帧 {frame['index']} (t={frame['timestamp']}s) 分析完成")
            
        except Exception as e:
            logger.error(f"[VISION] 帧 {frame['index']} 分析失败: {e}")
            analyses.append({
                'frame_index': frame['index'],
                'timestamp': frame['timestamp'],
                'description': None,
                'error': str(e),
                'success': False
            })
    
    return analyses


# ============================================================
# 第四部分：Whisper 音频转写（已有，增强版）
# ============================================================

def transcribe_audio(video_path: str, model: str = 'base', language: str = 'zh',
                     output_dir: Optional[str] = None) -> Dict:
    """
    使用 Whisper 转写视频音频（增强版）
    
    新增：支持使用 faster-whisper（如果可用），否则回退到标准 whisper
    """
    # 尝试 faster-whisper（更快的 CPU 推理）
    try:
        from faster_whisper import WhisperModel
        
        logger.info(f"[TRANSCRIBE] 使用 faster-whisper (model={model})")
        
        whisper_model = WhisperModel(model, device="cpu", compute_type="float32")
        segments, info = whisper_model.transcribe(
            video_path,
            language='zh' if language != 'auto' else None,
            beam_size=5,
            vad_filter=True
        )
        
        segments_list = list(segments)
        full_text = " ".join(seg.text for seg in segments_list)
        duration = segments_list[-1].end if segments_list else 0
        
        return {
            'success': True,
            'transcribed_text': full_text.strip(),
            'duration_sec': round(duration, 1),
            'segments': [
                {'start': round(s.start, 1), 'end': round(s.end, 1), 'text': s.text.strip()}
                for s in segments_list
            ],
            'word_count': len(full_text.replace(' ', '')),
            'language': info.language,
        }
        
    except ImportError:
        logger.info(f"[TRANSCRIBE] faster-whisper 不可用，回退到标准 whisper")
    
    # 回退到标准 whisper
    try:
        import whisper
        
        audio_model = whisper.load_model(model)
        result = audio_model.transcribe(
            video_path,
            language='zh' if language == 'auto' else language,
            task='transcribe',
            initial_prompt='以下是视频配音内容，请准确识别：'
        )
        
        full_text = result.get('text', '').strip()
        segments = result.get('segments', [])
        duration = segments[-1].get('end', 0) if segments else 0
        
        return {
            'success': True,
            'transcribed_text': full_text,
            'duration_sec': round(duration, 1),
            'segments': [
                {'start': round(s['start'], 1), 'end': round(s['end'], 1), 'text': s['text'].strip()}
                for s in segments
            ],
            'word_count': len(full_text.replace(' ', '')),
        }
        
    except ImportError:
        return {'success': False, 'error': 'Whisper 未安装'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


# ============================================================
# 第五部分：增强版拆解器
# ============================================================

class DouyinVideoDeconstructorV3:
    """
    抖音视频拆解器 v3 - 集成场景检测 + 关键帧提取 + 画面分析
    
    在 v2 基础上增加：
    1. PySceneDetect 场景切换检测
    2. OpenCV 自适应关键帧提取
    3. 预留 LLM Vision 画面分析接口
    """
    
    def __init__(self, whisper_model: str = 'base'):
        self.whisper_model = whisper_model
        self._analyzer = None
        self._temp_dir = None
    
    @property
    def analyzer(self):
        if self._analyzer is None:
            try:
                from modules.douyin_analyzer import DouyinAnalyzer
                self._analyzer = DouyinAnalyzer()
            except ImportError:
                # 从命令行执行时的路径修正
                sys.path.insert(0, os.path.join(_SCRIPT_DIR, 'modules'))
                from douyin_analyzer import DouyinAnalyzer
                self._analyzer = DouyinAnalyzer()
        return self._analyzer
    
    def deconstruct(self, share_url: str, transcribe: bool = False,
                    detect_scenes: bool = False, analyze_frames: bool = False,
                    vision_api_key: str = None) -> Dict:
        """
        拆解抖音视频（v3版）
        
        Args:
            share_url: 抖音分享链接
            transcribe: 是否转写音频
            detect_scenes: 是否检测场景切换
            analyze_frames: 是否提取关键帧
            vision_api_key: OpenRouter API Key（用于画面分析）
            
        Returns:
            dict: 结构化拆解报告
        """
        logger.info(f"[DECONSTRUCT v3] 开始拆解: {share_url}")
        
        # 第一步：获取原始数据
        raw = self.analyzer.analyze(share_url, download=True)
        if not raw.get('success'):
            return {'success': False, 'source': share_url, 'error': raw.get('error', '分析失败')}
        
        # 基础拆解
        report = self._build_base_report(raw)
        dims = report['dimensions']
        video_path = raw.get('file_path', '')
        
        # 第二步：场景检测
        if detect_scenes and video_path and os.path.exists(video_path):
            logger.info("[*] 检测场景切换...")
            scenes = detect_scenes(video_path)
            if scenes:
                report['dimensions']['scene_detection'] = {
                    'success': True,
                    'scene_count': len(scenes),
                    'scenes': scenes[:10],  # 只保留前10个
                    'avg_scene_duration': round(sum(s['duration'] for s in scenes) / max(len(scenes), 1), 1),
                }
        
        # 第三步：音频转写
        if transcribe and video_path and os.path.exists(video_path):
            logger.info("[*] 音频转写...")
            transcribe_result = transcribe_audio(video_path, model=self.whisper_model)
            dims['audio_transcription'] = transcribe_result
            if transcribe_result.get('success'):
                dims['audio_analysis']['voiceover_style'] = self._analyze_voiceover_style(transcribe_result)
        
        # 第四步：关键帧提取
        if analyze_frames and video_path and os.path.exists(video_path):
            logger.info("[*] 提取关键帧...")
            temp_dir = os.path.join(tempfile.gettempdir(), 'maphot_v3_frames',
                                    datetime.now().strftime('%Y%m%d_%H%M%S'))
            
            frames = extract_keyframes_adaptive(video_path, temp_dir, max_frames=15)
            
            if frames:
                report['dimensions']['frame_analysis'] = {
                    'success': True,
                    'frame_count': len(frames),
                    'frames': frames[:5],  # 只保留前5帧信息
                    'total_frames_extracted': len(frames),
                }
                
                # 第五步：画面分析（如果有API Key）
                if vision_api_key:
                    logger.info("[*] 画面视觉分析...")
                    vision_results = analyze_frames_with_vision(
                        frames, api_key=vision_api_key, max_frames=3
                    )
                    report['dimensions']['frame_vision_analysis'] = {
                        'success': True,
                        'analyses': vision_results
                    }
        
        # 评分
        report['score'] = self._score_v3(report)
        
        return report
    
    def _build_base_report(self, raw: Dict) -> Dict:
        """构建基础拆解报告"""
        report = {
            'success': True,
            'source_url': '',
            'deconstruct_time': datetime.now().isoformat(),
            'deconstructor': 'DouyinVideoDeconstructorV3',
            'dimensions': {}
        }
        
        stats = raw.get('statistics', {})
        title = raw.get('title', '')
        description = raw.get('description', '')
        
        report['dimensions']['video_meta'] = {
            'title': title,
            'duration_ms': raw.get('duration', 0),
            'duration_sec': round(raw.get('duration', 0) / 1000, 1),
            'resolution': raw.get('resolution', ''),
            'video_id': raw.get('video_id', ''),
            'description': description[:200],
        }
        
        report['dimensions']['author_profile'] = {
            'nickname': raw.get('author', ''),
            'uid': raw.get('author_id', ''),
            'signature': raw.get('signature', '')[:100],
        }
        
        total = sum([
            stats.get('digg_count', 0),
            stats.get('comment_count', 0),
            stats.get('share_count', 0),
            stats.get('collect_count', 0),
        ])
        report['dimensions']['engagement_metrics'] = {
            'digg_count': stats.get('digg_count', 0),
            'comment_count': stats.get('comment_count', 0),
            'share_count': stats.get('share_count', 0),
            'collect_count': stats.get('collect_count', 0),
            'total_interaction': total,
            'engagement_rate': round(total / max(stats.get('digg_count', 1), 1) * 100, 1) if stats.get('digg_count', 0) > 0 else 0,
        }
        
        content = self._analyze_content_structure(title, description)
        report['dimensions']['content_structure'] = content
        
        music = raw.get('music', {})
        report['dimensions']['audio_analysis'] = {
            'bgm_title': music.get('title', '') if music else '',
            'bgm_author': music.get('author', '') if music else '',
            'voiceover_style': None,
            'sound_effects': None,
        }
        
        tags = raw.get('tags', [])
        report['dimensions']['tag_cluster'] = {
            'tags': tags,
            'category': self._classify_category(tags, title),
            'keywords': self._extract_keywords(title, tags),
        }
        
        comments = raw.get('comments', [])
        report['dimensions']['comment_sentiment'] = self._analyze_comments(comments)
        
        report['dimensions']['reusable_template'] = {
            'template_type': None,
            'template_params': {},
            'applicable_to': [],
        }
        
        # 新增：场景检测和帧分析占位
        report['dimensions']['scene_detection'] = None
        report['dimensions']['frame_analysis'] = None
        report['dimensions']['frame_vision_analysis'] = None
        
        return report
    
    def _analyze_voiceover_style(self, transcribe_result: Dict) -> str:
        """分析配音风格"""
        if not transcribe_result.get('success'):
            return '无法分析'
        text = transcribe_result.get('transcribed_text', '')
        word_count = transcribe_result.get('word_count', 0)
        duration = transcribe_result.get('duration_sec', 1)
        if duration == 0:
            return '未知'
        words_per_sec = word_count / duration
        if words_per_sec > 5:
            pace = '快节奏'
        elif words_per_sec > 3:
            pace = '中快节奏'
        elif words_per_sec > 2:
            pace = '中等节奏'
        else:
            pace = '慢节奏'
        if '揭秘' in text or '分析' in text:
            style = '分析型'
        elif '感受' in text or '推荐' in text:
            style = '感受型'
        elif '你知道吗' in text:
            style = '科普型'
        elif '今天' in text or '最近' in text:
            style = '资讯型'
        else:
            style = '综合型'
        return f'{style} | {pace} | {words_per_sec:.1f}字/秒'
    
    def _analyze_content_structure(self, title: str, description: str) -> Dict:
        """分析内容结构"""
        text = f"{title} {description}"
        hook_patterns = {
            '数字型': r'\d+[个种类项条]',
            '反问型': r'(你知道吗|你见过|你了解|你有没有|为什么|难道|怎么)',
            '悬念型': r'(震惊|竟然|没想到|居然|太可怕|太震撼|太牛)',
            '对比型': r'(比.*更|最.*之一|最大|最小|最高|最低|排名|排行)',
            '排名型': r'(TOP|top|排名|排行|第[一二三四五六七八九十\d])',
            '地域型': r'(中国|全国|全球|城市|省份|地区)',
        }
        detected_hooks = [k for k, v in hook_patterns.items() if re.search(v, text)]
        
        body_patterns = {
            '数据罗列': r'(\d+[万亿]?[%％]|数据|统计|数据显示)',
            '排名对比': r'(排名|排行|第[一二三四五六七八九十\d]|TOP|top)',
            '故事叙述': r'(曾经|以前|后来|当时|有一天|记得)',
            '知识科普': r'(什么是|是什么|意思是|指的是|原理|机制)',
            '趋势分析': r'(增长|下降|上升|趋势|变化|越来越)',
        }
        detected_body = [k for k, v in body_patterns.items() if re.search(v, text)]
        
        cta_patterns = {
            '点赞': r'(点赞|双击|点个赞|小心心|爱心)',
            '关注': r'(关注|关注我|点关注|关注一下)',
            '评论': r'(评论|留言|说说|告诉)',
            '收藏': r'(收藏|保存|收好)',
            '分享': r'(分享|转发|@|艾特)',
        }
        detected_cta = [k for k, v in cta_patterns.items() if re.search(v, text)]
        
        return {
            'hook_type': detected_hooks[0] if detected_hooks else '未检测',
            'hook_types_all': detected_hooks,
            'body_structure': detected_body[0] if detected_body else '未检测',
            'body_structures_all': detected_body,
            'cta_types': detected_cta,
            'pacing': self._estimate_pacing(len(text)),
            'visual_style': '未检测',
            'visual_styles_all': [],
        }
    
    def _estimate_pacing(self, text_length: int) -> str:
        if text_length < 20:
            return '快节奏（短标题，信息密度高）'
        elif text_length < 50:
            return '中等节奏'
        else:
            return '慢节奏（长标题，铺垫较多）'
    
    def _classify_category(self, tags: List[str], title: str) -> str:
        text = f"{' '.join(tags)} {title}".lower()
        categories = {
            '城市/地理': ['城市', '地理', '地图', '区域', '省份', 'GDP', '经济', '人口'],
            '旅游/美食': ['旅游', '美食', '景点', '打卡', '旅行', '攻略'],
            '科技/数码': ['科技', '数码', '手机', 'AI', '人工智能', '互联网'],
            '财经/商业': ['财经', '经济', '商业', '投资', '股票', '理财', 'GDP'],
            '教育/知识': ['教育', '知识', '科普', '学习', '考试', '大学'],
            '社会/热点': ['社会', '热点', '新闻', '事件', '政策', '改革'],
            '生活/技巧': ['生活', '技巧', '实用', '干货', '教程', '方法'],
            '娱乐/搞笑': ['娱乐', '搞笑', '段子', '明星', '综艺', '影视'],
        }
        for category, keywords in categories.items():
            for kw in keywords:
                if kw in text:
                    return category
        return '未分类'
    
    def _extract_keywords(self, title: str, tags: List[str]) -> List[str]:
        words = []
        if title:
            parts = re.split(r'[，。！？、\s,.\!?]', title)
            words.extend(p for p in parts if len(p) >= 2)
        words.extend(tags)
        seen = set()
        return [w for w in words if not (w in seen or seen.add(w))][:10]
    
    def _analyze_comments(self, comments: List[Dict]) -> Dict:
        if not comments:
            return {'hot_comments': [], 'positive_ratio': 0, 'negative_ratio': 0, 'question_ratio': 0, 'comment_count': 0}
        positive_words = ['好', '赞', '厉害', '不错', '喜欢', '支持', '优秀', '精彩', '实用', '收藏']
        negative_words = ['差', '烂', '不行', '不好', '垃圾', '骗人', '假', '坑', '失望', '无聊']
        question_words = ['？', '?', '为什么', '怎么', '哪里', '什么', '如何', '吗']
        positive = negative = question = 0
        hot_comments = []
        for c in comments[:5]:
            text = c.get('text', '')
            hot_comments.append({'user': c.get('user', ''), 'text': text[:80], 'likes': c.get('digg_count', 0)})
            if any(w in text for w in positive_words): positive += 1
            if any(w in text for w in negative_words): negative += 1
            if any(w in text for w in question_words): question += 1
        total = len(comments)
        return {
            'hot_comments': hot_comments,
            'positive_ratio': round(positive / max(total, 1) * 100, 1),
            'negative_ratio': round(negative / max(total, 1) * 100, 1),
            'question_ratio': round(question / max(total, 1) * 100, 1),
            'comment_count': total,
        }
    
    def _score_v3(self, report: Dict) -> float:
        """v3 评分（增加场景检测和帧分析权重）"""
        dims = report.get('dimensions', {})
        score = 0
        
        # 互动分（35%）
        metrics = dims.get('engagement_metrics', {})
        total = metrics.get('total_interaction', 0)
        if total > 0:
            import math
            score += 35 * min(1, math.log10(total / 10000 + 1))
        
        # 结构分（25%）
        content = dims.get('content_structure', {})
        if content.get('hook_type') != '未检测': score += 8
        if content.get('body_structure') != '未检测': score += 8
        if content.get('cta_types'): score += 4
        if content.get('visual_style') != '未检测': score += 5
        score += min(5, len(content.get('hook_types_all', [])) * 2)
        
        # 标签分（10%）
        tags = dims.get('tag_cluster', {})
        score += min(10, len(tags.get('tags', [])) * 2)
        
        # 评论分（10%）
        comments = dims.get('comment_sentiment', {})
        score += min(10, comments.get('comment_count', 0) * 3)
        
        # 场景检测加分（10%）
        scenes = dims.get('scene_detection', {})
        if scenes and scenes.get('success'):
            score += min(10, scenes.get('scene_count', 0) * 2)
        
        # 转写加分（5%）
        transcribe = dims.get('audio_transcription', {})
        if transcribe.get('success'):
            score += 5
        
        # 帧分析加分（5%）
        frames = dims.get('frame_analysis', {})
        if frames and frames.get('success'):
            score += 5
        
        return round(min(100, score), 1)
    
    def generate_template(self, report: Dict) -> Optional[Dict]:
        """生成可复用模板"""
        if not report.get('success'):
            return None
        dims = report.get('dimensions', {})
        content = dims.get('content_structure', {})
        transcribe = dims.get('audio_transcription', {})
        scenes = dims.get('scene_detection', {})
        frames = dims.get('frame_analysis', {})
        
        template_type = '综合展示'
        body = content.get('body_structure', '')
        if '排名' in body or '对比' in body:
            template_type = '排行榜'
        elif '数据' in body:
            template_type = '数据可视化'
        elif '科普' in body or '知识' in body:
            template_type = '知识科普'
        elif '趋势' in body:
            template_type = '趋势分析'
        elif '故事' in body:
            template_type = '故事叙述'
        
        template = {
            'template_type': template_type,
            'source_video': dims.get('video_meta', {}).get('title', ''),
            'source_duration': dims.get('video_meta', {}).get('duration_sec', 0),
            'source_score': report.get('score', 0),
            'params': {
                'hook_style': content.get('hook_type', ''),
                'body_style': content.get('body_structure', ''),
                'pacing': content.get('pacing', ''),
                'cta_style': content.get('cta_types', []),
                'target_duration': self._calc_target_duration(dims.get('video_meta', {}).get('duration_sec', 0)),
            },
            'voiceover': {
                'text': transcribe.get('transcribed_text', '')[:500],
                'word_count': transcribe.get('word_count', 0),
                'duration_sec': transcribe.get('duration_sec', 0),
            } if transcribe.get('success') else None,
            'scene_analysis': {
                'scene_count': scenes.get('scene_count', 0) if scenes else 0,
                'avg_scene_duration': scenes.get('avg_scene_duration', 0) if scenes else 0,
            } if scenes and scenes.get('success') else None,
            'frame_analysis': {
                'frame_count': frames.get('frame_count', 0) if frames else 0,
            } if frames and frames.get('success') else None,
            'applicable_to': ['城市综合展示'],
            'suggestion': self._generate_suggestion(report),
        }
        report['dimensions']['reusable_template'] = template
        return template
    
    def _calc_target_duration(self, source_duration: float) -> int:
        if source_duration <= 0: return 30
        if source_duration < 15: return 15
        elif source_duration < 30: return 30
        elif source_duration < 60: return 45
        else: return 60
    
    def _generate_suggestion(self, report: Dict) -> List[str]:
        dims = report.get('dimensions', {})
        content = dims.get('content_structure', {})
        metrics = dims.get('engagement_metrics', {})
        suggestions = []
        if content.get('hook_type') == '未检测':
            suggestions.append('建议添加明确的钩子开头')
        if not content.get('cta_types'):
            suggestions.append('建议添加引导互动')
        meta = dims.get('video_meta', {})
        duration = meta.get('duration_sec', 0)
        if duration > 60:
            suggestions.append(f'视频较长({duration:.0f}s)，建议控制在30-45秒')
        total = metrics.get('total_interaction', 0)
        if total < 1000:
            suggestions.append('互动量偏低，可优化标题')
        if not suggestions:
            suggestions.append('内容结构完整')
        return suggestions


# ============================================================
# 快速入口函数
# ============================================================

def deconstruct_video_v3(share_url: str, transcribe: bool = False,
                         detect_scenes: bool = False, analyze_frames: bool = False,
                         vision_api_key: str = None, model: str = 'base') -> Dict:
    """快速拆解抖音视频（v3版）"""
    dc = DouyinVideoDeconstructorV3(whisper_model=model)
    return dc.deconstruct(share_url, transcribe=transcribe,
                          detect_scenes=detect_scenes,
                          analyze_frames=analyze_frames,
                          vision_api_key=vision_api_key)


def generate_template_v3(share_url: str, transcribe: bool = False,
                         detect_scenes: bool = False, analyze_frames: bool = False,
                         vision_api_key: str = None, model: str = 'base') -> Optional[Dict]:
    """从抖音视频生成可复用模板（v3版）"""
    dc = DouyinVideoDeconstructorV3(whisper_model=model)
    report = dc.deconstruct(share_url, transcribe=transcribe,
                            detect_scenes=detect_scenes,
                            analyze_frames=analyze_frames,
                            vision_api_key=vision_api_key)
    if report.get('success'):
        return dc.generate_template(report)
    return None


# ============================================================
# 测试入口
# ============================================================
if __name__ == '__main__':
    import sys
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    if len(sys.argv) < 2:
        print("用法: python deconstruct_v3.py <抖音分享链接> [选项]")
        print("  --transcribe: 转写音频")
        print("  --scenes: 检测场景切换")
        print("  --frames: 提取关键帧")
        print("  --vision: 画面分析（需API Key）")
        print("  --model: Whisper模型 (base/small/medium/large)")
        sys.exit(1)
    
    share_url = sys.argv[1]
    transcribe = '--transcribe' in sys.argv
    detect_scenes = '--scenes' in sys.argv
    analyze_frames = '--frames' in sys.argv
    use_vision = '--vision' in sys.argv
    
    model = 'base'
    if '--model' in sys.argv:
        idx = sys.argv.index('--model')
        if idx + 1 < len(sys.argv):
            model = sys.argv[idx + 1]
    
    # 获取 vision API Key（如果使用）
    vision_key = None
    if use_vision:
        try:
            vision_key = os.environ.get('OPENROUTER_API_KEY', '')
        except:
            pass
    
    try:
        report = deconstruct_video_v3(share_url, transcribe=transcribe,
                                      detect_scenes=detect_scenes,
                                      analyze_frames=analyze_frames,
                                      vision_api_key=vision_key, model=model)
        if report.get('success'):
            _print_report(report)
        else:
            print(f"[X] 拆解失败: {report.get('error', '')}")
    except Exception as e:
        print(f"[X] 错误: {e}")
        import traceback
        traceback.print_exc()


def _print_report(report: Dict):
    """格式化输出拆解报告"""
    dims = report.get('dimensions', {})
    meta = dims.get('video_meta', {})
    metrics = dims.get('engagement_metrics', {})
    content = dims.get('content_structure', {})
    
    print(f"\n[VIDEO] {meta.get('title', '')[:60]}")
    print(f"[TIME] {meta.get('duration_sec', 0):.1f}s")
    print(f"[SCORE] {report.get('score', 0):.0f}/100")
    print(f"[AUTHOR] {dims.get('author_profile', {}).get('nickname', '')}")
    
    print(f"\n[STATS] 点赞:{metrics.get('digg_count', 0):,} | 评论:{metrics.get('comment_count', 0):,} | 分享:{metrics.get('share_count', 0):,} | 收藏:{metrics.get('collect_count', 0):,}")
    
    print(f"\n[STRUCTURE] 钩子:{content.get('hook_type', '')} | 正文:{content.get('body_structure', '')} | CTA:{', '.join(content.get('cta_types', ['无']))}")
    
    # 场景检测
    scenes = dims.get('scene_detection', {})
    if scenes and scenes.get('success'):
        print(f"\n[SCENES] {scenes.get('scene_count', 0)} 个场景切换 | 平均时长:{scenes.get('avg_scene_duration', 0)}s")
        for s in scenes.get('scenes', [])[:3]:
            print(f"  > 场景 {s['scene_index']}: {s.get('start_timecode', '')} -> {s.get('end_timecode', '')} ({s.get('duration', 0)}s)")
    
    # 转写
    transcribe = dims.get('audio_transcription', {})
    if transcribe.get('success'):
        print(f"\n[TRANSCRIBE] {transcribe.get('word_count', 0)}字 | {transcribe.get('duration_sec', 0):.1f}s")
        print(f"  {transcribe.get('transcribed_text', '')[:200]}...")
        voice = dims.get('audio_analysis', {}).get('voiceover_style', '')
        if voice:
            print(f"  [STYLE] {voice}")
    
    # 关键帧
    frames = dims.get('frame_analysis', {})
    if frames and frames.get('success'):
        print(f"\n[FRAMES] 提取 {frames.get('frame_count', 0)} 个关键帧")
        for f in frames.get('frames', [])[:3]:
            print(f"  > 帧 {f.get('index', 0)}: t={f.get('timestamp', 0)}s, score={f.get('score', 0)}")
    
    # 画面分析
    vision = dims.get('frame_vision_analysis', {})
    if vision and vision.get('success'):
        print(f"\n[VISION] 画面分析:")
        for a in vision.get('analyses', []):
            if a.get('success'):
                print(f"  > 帧 {a.get('frame_index', 0)} (t={a.get('timestamp', 0)}s): {a.get('description', '')[:100]}...")
    
    # 标签
    tags = dims.get('tag_cluster', {})
    print(f"\n[TAGS] {', '.join(tags.get('tags', []))} | {tags.get('category', '')}")
    
    # 评论
    comments = dims.get('comment_sentiment', {})
    if comments.get('hot_comments'):
        print(f"\n[COMMENTS] ({comments.get('comment_count', 0)}条):")
        for c in comments['hot_comments'][:3]:
            print(f"  @{c['user']}: {c['text'][:50]}")
    
    # 模板
    template = dims.get('reusable_template', {})
    if template.get('template_type'):
        print(f"\n[TEMPLATE] {template['template_type']}")
        if template.get('suggestion'):
            print(f"  [SUGGEST] {template['suggestion'][0]}")