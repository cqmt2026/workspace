# -*- coding: utf-8 -*-
"""
抖音视频拆解增强版 - 支持配音转写 + 关键帧分析
=================================================
在原始 deconstruct.py 基础上增加：
1. Whisper 音频转写 → 获取配音文案
2. FFmpeg 关键帧提取 + vision 分析 → 获取画面描述

依赖：
- whisper (已安装)
- ffmpeg (已安装)
- modules.douyin_analyzer (已有)

用法：
    from modules.deconstruct_v2 import DouyinVideoDeconstructorV2, deconstruct_video_v2
    
    # 拆解单条视频（含转写和帧分析）
    report = deconstruct_video_v2("https://v.douyin.com/xxx/", transcribe=True, analyze_frames=True)
"""

import json
import os
import logging
import re
import subprocess
import tempfile
from datetime import datetime
from typing import Optional, List, Dict

# 延迟导入，避免循环依赖
logger = logging.getLogger(__name__)

# ============================================================
# Whisper 转写模块
# ============================================================

def transcribe_audio(video_path: str, model: str = 'base', language: str = 'zh', 
                     output_dir: Optional[str] = None) -> Dict:
    """
    使用 Whisper 转写视频音频
    
    Args:
        video_path: 视频文件路径
        model: Whisper 模型大小（base/small/medium/large）
        language: 识别语言（zh/en/auto）
        output_dir: 输出目录（默认临时目录）
        
    Returns:
        dict: 包含 transcribed_text, duration_sec, segments 等
    """
    try:
        import whisper
        
        logger.info(f"[TRANS] 开始音频转写: {video_path} (model={model}, lang={language})")
        
        # 加载模型
        audio_model = whisper.load_model(model)
        
        # 执行转写
        result = audio_model.transcribe(
            video_path,
            language='zh' if language == 'auto' else language,
            task='transcribe',
            word_timestamps=False,
            initial_prompt='以下是视频配音内容，请准确识别：'
        )
        
        # 提取结果
        full_text = result.get('text', '').strip()
        duration = result.get('segments', [{}])[-1].get('end', 0) if result.get('segments') else 0
        
        # 分段信息
        segments = []
        for seg in result.get('segments', []):
            segments.append({
                'start': round(seg['start'], 1),
                'end': round(seg['end'], 1),
                'text': seg['text'].strip()
            })
        
        logger.info(f"[OK] 转写完成: {len(full_text)} 字, {duration:.1f}s, {len(segments)} 段")
        
        return {
            'success': True,
            'transcribed_text': full_text,
            'duration_sec': round(duration, 1),
            'segments': segments,
            'word_count': len(full_text.replace(' ', '')),
            'avg_sentence_length': len(full_text.replace(' ', '')) / max(len(segments), 1),
        }
        
    except ImportError:
        return {
            'success': False,
            'error': 'Whisper 未安装，运行: pip install openai-whisper'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


# ============================================================
# 关键帧提取 + 分析模块
# ============================================================

def extract_keyframes(video_path: str, output_dir: str, interval: float = 3.0, 
                      max_frames: int = 10) -> List[Dict]:
    """
    使用 FFmpeg 提取关键帧
    
    Args:
        video_path: 视频文件路径
        output_dir: 输出目录
        interval: 帧提取间隔（秒）
        max_frames: 最大提取帧数
        
    Returns:
        list: 提取的帧信息列表
    """
    os.makedirs(output_dir, exist_ok=True)
    frames = []
    
    try:
        # 使用 ffmpeg 按固定间隔提取帧
        cmd = [
            'ffmpeg', '-i', video_path,
            '-vf', f'fps=1/{interval}',
            '-q:v', '2',  # 高质量
            '-frames:v', str(max_frames),
            os.path.join(output_dir, 'frame_%04d.jpg')
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            logger.warning(f"FFmpeg 提取帧失败: {result.stderr[:200]}")
            return []
        
        # 扫描输出目录
        import glob
        frame_files = sorted(glob.glob(os.path.join(output_dir, 'frame_*.jpg')))
        
        for i, frame_file in enumerate(frame_files):
            frames.append({
                'index': i,
                'path': frame_file,
                'filename': os.path.basename(frame_file)
            })
        
        logger.info(f"[OK] 提取了 {len(frames)} 帧")
        return frames
        
    except Exception as e:
        logger.error(f"提取关键帧失败: {e}")
        return []


def analyze_frames_with_image_tool(frames: List[Dict]) -> List[Dict]:
    """
    使用 image 工具分析关键帧内容
    
    注意：此函数需要在有 image 工具可用时调用
    返回格式化的帧分析结果
    """
    analyses = []
    
    for frame in frames:
        try:
            # 调用 image 工具分析（通过 exec 模拟，实际应调用工具）
            # 这里先返回占位，实际调用需要在完整环境中实现
            analyses.append({
                'frame_index': frame['index'],
                'path': frame['path'],
                'analysis': '需要调用 image 工具进行分析'
            })
        except Exception as e:
            analyses.append({
                'frame_index': frame['index'],
                'path': frame['path'],
                'error': str(e)
            })
    
    return analyses


# ============================================================
# 增强版拆解器
# ============================================================

class DouyinVideoDeconstructorV2:
    """
    增强版抖音视频拆解器
    
    在原始拆解基础上增加：
    1. Whisper 音频转写 → 获取配音文案和节奏
    2. 关键帧提取 → 分析画面内容
    """
    
    def __init__(self, whisper_model: str = 'base'):
        self.whisper_model = whisper_model
        self._analyzer = None
        self._temp_dir = None
    
    @property
    def analyzer(self):
        if self._analyzer is None:
            # 动态添加项目路径，确保从命令行也能正确导入 modules.douyin_analyzer
            import sys as _sys
            _module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if _module_dir not in _sys.path:
                _sys.path.insert(0, _module_dir)
            from modules.douyin_analyzer import DouyinAnalyzer
            self._analyzer = DouyinAnalyzer()
        return self._analyzer
    
    def deconstruct(self, share_url: str, transcribe: bool = False, 
                    analyze_frames: bool = False) -> Dict:
        """
        拆解抖音视频（增强版）
        
        Args:
            share_url: 抖音分享链接
            transcribe: 是否转写音频（需要下载视频）
            analyze_frames: 是否分析关键帧（需要下载视频）
            
        Returns:
            dict: 结构化拆解报告
        """
        logger.info(f"[DECONSTRUCT] 开始增强版拆解: {share_url}")
        
        # 第一步：获取原始数据（自动下载视频以便转写）
        raw = self.analyzer.analyze(share_url, download=True)
        if not raw.get('success'):
            return {'success': False, 'source': share_url, 'error': raw.get('error', '分析失败')}
        
        # 基础拆解（复用原有逻辑）
        report = self._build_base_report(raw)
        
        # 第二步：音频转写
        if transcribe and raw.get('file_path'):
            logger.info("[TRANS] 执行音频转写...")
            transcribe_result = transcribe_audio(raw['file_path'], model=self.whisper_model)
            report['dimensions']['audio_transcription'] = transcribe_result
            report['dimensions']['audio_analysis']['voiceover_style'] = self._analyze_voiceover_style(transcribe_result)
        
        # 第三步：关键帧分析
        if analyze_frames and raw.get('file_path'):
            logger.info("[FRAME] 提取关键帧...")
            temp_dir = os.path.join(tempfile.gettempdir(), 'maphot_frames', datetime.now().strftime('%Y%m%d_%H%M%S'))
            frames = extract_keyframes(raw['file_path'], temp_dir)
            report['dimensions']['frame_analysis'] = {
                'success': True,
                'frame_count': len(frames),
                'frames': frames
            }
            report['dimensions']['content_structure']['visual_style'] = self._analyze_visual_style(frames)
        
        # 评分（增强版）
        report['score'] = self._score_v2(report)
        
        return report
    
    def _build_base_report(self, raw: Dict) -> Dict:
        """构建基础拆解报告（复用原有逻辑）"""
        from datetime import datetime
        
        report = {
            'success': True,
            'source_url': '',
            'deconstruct_time': datetime.now().isoformat(),
            'deconstructor': 'DouyinVideoDeconstructorV2',
            'dimensions': {}
        }
        
        # 元数据
        report['dimensions']['video_meta'] = {
            'title': raw.get('title', ''),
            'duration_ms': raw.get('duration', 0),
            'duration_sec': round(raw.get('duration', 0) / 1000, 1),
            'resolution': raw.get('resolution', ''),
            'video_id': raw.get('video_id', ''),
            'description': raw.get('description', '')[:200],
        }
        
        # 作者画像
        report['dimensions']['author_profile'] = {
            'nickname': raw.get('author', ''),
            'uid': raw.get('author_id', ''),
            'signature': raw.get('signature', '')[:100],
        }
        
        # 互动数据
        stats = raw.get('statistics', {})
        total = (
            stats.get('digg_count', 0) +
            stats.get('comment_count', 0) +
            stats.get('share_count', 0) +
            stats.get('collect_count', 0)
        )
        report['dimensions']['engagement_metrics'] = {
            'digg_count': stats.get('digg_count', 0),
            'comment_count': stats.get('comment_count', 0),
            'share_count': stats.get('share_count', 0),
            'collect_count': stats.get('collect_count', 0),
            'total_interaction': total,
            'engagement_rate': round(total / max(stats.get('digg_count', 1), 1) * 100, 1) if stats.get('digg_count', 0) > 0 else 0,
        }
        
        # 内容结构
        title = raw.get('title', '')
        description = raw.get('description', '')
        report['dimensions']['content_structure'] = self._analyze_content_structure(title, description)
        
        # 音频分析
        music = raw.get('music', {})
        report['dimensions']['audio_analysis'] = {
            'bgm_title': music.get('title', '') if music else '',
            'bgm_author': music.get('author', '') if music else '',
            'voiceover_style': None,
            'sound_effects': None,
        }
        
        # 标签聚类
        tags = raw.get('tags', [])
        report['dimensions']['tag_cluster'] = {
            'tags': tags,
            'category': self._classify_category(tags, title),
            'keywords': self._extract_keywords(title, tags),
        }
        
        # 评论情感
        comments = raw.get('comments', [])
        report['dimensions']['comment_sentiment'] = self._analyze_comments(comments)
        
        # 可复用模板
        report['dimensions']['reusable_template'] = {
            'template_type': None,
            'template_params': {},
            'applicable_to': [],
        }
        
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
        
        # 语速分析
        words_per_sec = word_count / duration
        
        if words_per_sec > 5:
            pace = '快节奏'
        elif words_per_sec > 3:
            pace = '中快节奏'
        elif words_per_sec > 2:
            pace = '中等节奏'
        else:
            pace = '慢节奏'
        
        # 风格判断（简化版，实际可根据内容进一步分析）
        if '揭秘' in text or '分析' in text:
            style = '分析型'
        elif '感受' in text or '推荐' in text:
            style = '感受型'
        elif '你知道吗' in text or '你知道吗' in text:
            style = '科普型'
        elif '今天' in text or '最近' in text:
            style = '资讯型'
        else:
            style = '综合型'
        
        return f'{style} | {pace} | {words_per_sec:.1f}字/秒'
    
    def _analyze_visual_style(self, frames: List[Dict]) -> str:
        """分析视觉风格"""
        if not frames:
            return '未提取到关键帧'
        
        # 根据帧的特征推断风格（简化版）
        styles = []
        
        # 检查是否有地图元素
        for frame in frames[:3]:  # 检查前3帧
            if '地图' in frame.get('analysis', '') or 'chart' in frame.get('analysis', '').lower():
                styles.append('数据可视化')
                break
        
        if not styles:
            styles.append('综合展示')
        
        return ' + '.join(styles)
    
    def _analyze_content_structure(self, title: str, description: str) -> Dict:
        """分析内容结构"""
        text = f"{title} {description}"
        
        # 检测钩子类型
        hook_patterns = {
            '数字型': r'\d+[个种类项条]',
            '反问型': r'(你知道吗|你见过|你了解|你有没有|为什么|难道|怎么)',
            '悬念型': r'(震惊|竟然|没想到|居然|太可怕|太震撼|太牛)',
            '对比型': r'(比.*更|最.*之一|最大|最小|最高|最低|排名|排行)',
            '排名型': r'(TOP|top|排名|排行|第[一二三四五六七八九十\d])',
            '地域型': r'(中国|全国|全球|城市|省份|地区)',
        }
        detected_hooks = []
        for hook_type, pattern in hook_patterns.items():
            if re.search(pattern, text):
                detected_hooks.append(hook_type)
        
        # 检测正文结构
        body_patterns = {
            '数据罗列': r'(\d+[万亿]?[%％]|数据|统计|数据显示)',
            '排名对比': r'(排名|排行|第[一二三四五六七八九十\d]|TOP|top)',
            '故事叙述': r'(曾经|以前|后来|当时|有一天|记得)',
            '知识科普': r'(什么是|是什么|意思是|指的是|原理|机制)',
            '趋势分析': r'(增长|下降|上升|趋势|变化|越来越)',
        }
        detected_body = []
        for body_type, pattern in body_patterns.items():
            if re.search(pattern, text):
                detected_body.append(body_type)
        
        # 检测CTA
        cta_patterns = {
            '点赞': r'(点赞|双击|点个赞|小心心|爱心)',
            '关注': r'(关注|关注我|点关注|关注一下)',
            '评论': r'(评论|留言|说说|告诉)',
            '收藏': r'(收藏|保存|收好)',
            '分享': r'(分享|转发|@|艾特)',
        }
        detected_cta = []
        for cta_type, pattern in cta_patterns.items():
            if re.search(pattern, text):
                detected_cta.append(cta_type)
        
        # 视觉风格推断
        visual_keywords = {
            '地图': ['地图', '分布', '区域', '覆盖'],
            '数据图表': ['数据', '统计', '比例', '占比', '排名'],
            '实拍': ['现场', '实拍', '航拍', '镜头'],
            '动画': ['动画', '示意图', '动态'],
        }
        detected_visual = []
        for style, kws in visual_keywords.items():
            for kw in kws:
                if kw in text:
                    detected_visual.append(style)
                    break
        
        return {
            'hook_type': detected_hooks[0] if detected_hooks else '未检测',
            'hook_types_all': detected_hooks,
            'body_structure': detected_body[0] if detected_body else '未检测',
            'body_structures_all': detected_body,
            'cta_types': detected_cta,
            'pacing': self._estimate_pacing(len(text)),
            'visual_style': detected_visual[0] if detected_visual else '未检测',
            'visual_styles_all': detected_visual,
        }
    
    def _estimate_pacing(self, text_length: int) -> str:
        """估算视频节奏"""
        if text_length < 20:
            return '快节奏（短标题，信息密度高）'
        elif text_length < 50:
            return '中等节奏'
        else:
            return '慢节奏（长标题，铺垫较多）'
    
    def _classify_category(self, tags: List[str], title: str) -> str:
        """分类"""
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
        """提取关键词"""
        words = []
        if title:
            parts = re.split(r'[，。！？、\s,.\!?]', title)
            for part in parts:
                if len(part) >= 2:
                    words.append(part)
        words.extend(tags)
        
        seen = set()
        unique = []
        for w in words:
            if w not in seen:
                seen.add(w)
                unique.append(w)
        return unique[:10]
    
    def _analyze_comments(self, comments: List[Dict]) -> Dict:
        """分析评论情感"""
        if not comments:
            return {
                'hot_comments': [],
                'positive_ratio': 0,
                'negative_ratio': 0,
                'question_ratio': 0,
                'comment_count': 0,
            }
        
        positive_words = ['好', '赞', '厉害', '不错', '喜欢', '支持', '优秀', '精彩', '实用', '收藏']
        negative_words = ['差', '烂', '不行', '不好', '垃圾', '骗人', '假', '坑', '失望', '无聊']
        question_words = ['？', '?', '为什么', '怎么', '哪里', '什么', '如何', '吗']
        
        positive = 0
        negative = 0
        question = 0
        
        hot_comments = []
        for c in comments[:5]:
            text = c.get('text', '')
            digg = c.get('digg_count', 0)
            hot_comments.append({
                'user': c.get('user', ''),
                'text': text[:80],
                'likes': digg,
            })
            
            for word in positive_words:
                if word in text:
                    positive += 1
                    break
            for word in negative_words:
                if word in text:
                    negative += 1
                    break
            for word in question_words:
                if word in text:
                    question += 1
                    break
        
        total = len(comments)
        return {
            'hot_comments': hot_comments,
            'positive_ratio': round(positive / max(total, 1) * 100, 1),
            'negative_ratio': round(negative / max(total, 1) * 100, 1),
            'question_ratio': round(question / max(total, 1) * 100, 1),
            'comment_count': total,
        }
    
    def _score_v2(self, report: Dict) -> float:
        """增强版评分"""
        dims = report.get('dimensions', {})
        score = 0
        
        # 互动分（40%）
        metrics = dims.get('engagement_metrics', {})
        total = metrics.get('total_interaction', 0)
        if total > 0:
            if total < 10000:
                interaction_score = total / 10000 * 40
            else:
                import math
                interaction_score = 40 * min(1, math.log10(total / 10000) + 1)
        else:
            interaction_score = 0
        score += interaction_score
        
        # 结构分（30%）
        content = dims.get('content_structure', {})
        structure_score = 0
        if content.get('hook_type') != '未检测':
            structure_score += 10
        if content.get('body_structure') != '未检测':
            structure_score += 10
        if content.get('cta_types'):
            structure_score += 5
        if content.get('visual_style') != '未检测':
            structure_score += 5
        score += structure_score
        
        # 标签分（10%）
        tags = dims.get('tag_cluster', {})
        tag_score = min(10, len(tags.get('tags', [])) * 2)
        score += tag_score
        
        # 评论分（10%）
        comments = dims.get('comment_sentiment', {})
        comment_score = min(10, comments.get('comment_count', 0) * 3)
        score += comment_score
        
        # 转写加分（10%）- 有新维度时加
        transcribe = dims.get('audio_transcription', {})
        if transcribe.get('success'):
            score += 10
        
        # 帧分析加分（10%）- 有新维度时加
        frame_analysis = dims.get('frame_analysis', {})
        if frame_analysis.get('success') and frame_analysis.get('frame_count', 0) > 0:
            score += 10
        
        return round(min(100, score), 1)
    
    def generate_template(self, report: Dict) -> Optional[Dict]:
        """生成可复用模板"""
        if not report.get('success'):
            return None
        
        dims = report.get('dimensions', {})
        meta = dims.get('video_meta', {})
        content = dims.get('content_structure', {})
        tags = dims.get('tag_cluster', {})
        transcribe = dims.get('audio_transcription', {})
        
        # 判断模板类型
        template_type = self._determine_template_type(content, tags, transcribe)
        
        # 提取配音文案（如果有）
        voiceover_text = ''
        if transcribe.get('success'):
            voiceover_text = transcribe.get('transcribed_text', '')
        
        # 生成参数化模板
        template = {
            'template_type': template_type,
            'source_video': meta.get('title', ''),
            'source_duration': meta.get('duration_sec', 0),
            'source_score': report.get('score', 0),
            
            'params': {
                'hook_style': content.get('hook_type', ''),
                'body_style': content.get('body_structure', ''),
                'pacing': content.get('pacing', ''),
                'visual_style': content.get('visual_style', ''),
                'cta_style': content.get('cta_types', []),
                'target_duration': self._calc_target_duration(meta.get('duration_sec', 0)),
            },
            
            # 新增：配音文案
            'voiceover': {
                'text': voiceover_text[:500],  # 只保留前500字
                'word_count': transcribe.get('word_count', 0),
                'duration_sec': transcribe.get('duration_sec', 0),
                'pace': transcribe.get('_voiceover_style', ''),
            } if transcribe.get('success') else None,
            
            # 适用场景
            'applicable_to': self._calc_applicable_scenarios(template_type, content, transcribe),
            
            # 改进建议
            'suggestion': self._generate_suggestion(report),
        }
        
        report['dimensions']['reusable_template'] = template
        return template
    
    def _determine_template_type(self, content: Dict, tags: List[str], 
                                  transcribe: Dict) -> str:
        """判断模板类型"""
        body = content.get('body_structure', '')
        visual = content.get('visual_style', '')
        tag_list = tags if isinstance(tags, list) else []
        
        # 检查配音文案
        voiceover_text = ''
        if transcribe.get('success'):
            voiceover_text = transcribe.get('transcribed_text', '')
        
        text = f"{body} {visual} {' '.join(tag_list)} {voiceover_text}"
        
        if '排名' in text or '对比' in text:
            return '排行榜'
        elif '数据' in text:
            return '数据可视化'
        elif '地图' in text:
            return '地图展示'
        elif '科普' in text or '知识' in text:
            return '知识科普'
        elif '趋势' in text:
            return '趋势分析'
        elif '故事' in text:
            return '故事叙述'
        else:
            return '综合展示'
    
    def _calc_target_duration(self, source_duration: float) -> int:
        """计算推荐时长"""
        if source_duration <= 0:
            return 30
        
        if source_duration < 15:
            return 15
        elif source_duration < 30:
            return 30
        elif source_duration < 60:
            return 45
        else:
            return 60
    
    def _calc_applicable_scenarios(self, template_type: str, content: Dict,
                                    transcribe: Dict) -> List[str]:
        """计算适用场景"""
        voiceover_text = ''
        if transcribe.get('success'):
            voiceover_text = transcribe.get('transcribed_text', '')
        
        scenarios = []
        
        if template_type == '排行榜':
            scenarios.extend(['城市GDP排名', '人口排名', '面积排名'])
        elif template_type == '数据可视化':
            scenarios.extend(['经济数据展示', '人口数据对比', '区域发展对比'])
        elif template_type == '地图展示':
            scenarios.extend(['区域分布图', '热点地图', '城市地图'])
        elif template_type == '知识科普':
            scenarios.extend(['城市历史', '地理知识', '区域特色'])
        elif template_type == '趋势分析':
            scenarios.extend(['经济趋势', '人口变化', '发展预测'])
        else:
            scenarios.append('城市综合展示')
        
        # 如果有配音文案，提取关键词作为额外场景
        if voiceover_text:
            keywords = re.findall(r'[\u4e00-\u9fa5]{2,4}', voiceover_text)
            scenarios.extend(keywords[:3])
        
        return list(set(scenarios))
    
    def _generate_suggestion(self, report: Dict) -> List[str]:
        """生成改进建议"""
        dims = report.get('dimensions', {})
        content = dims.get('content_structure', {})
        metrics = dims.get('engagement_metrics', {})
        transcribe = dims.get('audio_transcription', {})
        
        suggestions = []
        
        # 结构建议
        if content.get('hook_type') == '未检测':
            suggestions.append('建议添加明确的钩子开头（数字型/反问型/悬念型）')
        if not content.get('cta_types'):
            suggestions.append('建议添加引导互动（点赞/关注/评论）')
        
        # 时长建议
        meta = dims.get('video_meta', {})
        duration = meta.get('duration_sec', 0)
        if duration > 60:
            suggestions.append(f'视频较长({duration:.0f}s)，建议控制在30-45秒')
        elif duration < 15:
            suggestions.append(f'视频较短({duration:.0f}s)，可适当增加信息密度')
        
        # 互动建议
        total = metrics.get('total_interaction', 0)
        if total < 1000:
            suggestions.append('互动量偏低，可优化标题吸引力和内容质量')
        elif total < 10000:
            suggestions.append('互动量中等，可尝试增加争议性话题或实用信息')
        
        # 配音建议（如果有转写）
        if transcribe.get('success'):
            word_count = transcribe.get('word_count', 0)
            duration = transcribe.get('duration_sec', 0)
            if duration > 0:
                pace = word_count / duration
                if pace > 5:
                    suggestions.append(f'语速较快({pace:.1f}字/秒)，建议适当放慢')
                elif pace < 2.5:
                    suggestions.append(f'语速较慢({pace:.1f}字/秒)，建议加快节奏')
                else:
                    suggestions.append(f'语速适中({pace:.1f}字/秒)')
        
        if not suggestions:
            suggestions.append('内容结构完整，可保持当前风格')
        
        return suggestions


# ============================================================
# 快速入口函数
# ============================================================

def deconstruct_video_v2(share_url: str, transcribe: bool = False, 
                         analyze_frames: bool = False, model: str = 'base') -> Dict:
    """
    快速拆解抖音视频（增强版）
    
    Args:
        share_url: 抖音分享链接
        transcribe: 是否转写音频
        analyze_frames: 是否分析关键帧
        model: Whisper模型大小
        
    Returns:
        dict: 结构化拆解报告
    """
    deconstructor = DouyinVideoDeconstructorV2(whisper_model=model)
    return deconstructor.deconstruct(share_url, transcribe=transcribe, 
                                      analyze_frames=analyze_frames)


def generate_template_v2(share_url: str, transcribe: bool = False,
                         analyze_frames: bool = False, model: str = 'base') -> Optional[Dict]:
    """
    从抖音视频生成可复用模板（增强版）
    
    Args:
        share_url: 抖音分享链接
        transcribe: 是否转写音频
        analyze_frames: 是否分析关键帧
        model: Whisper模型大小
        
    Returns:
        dict: 可复用模板
    """
    deconstructor = DouyinVideoDeconstructorV2(whisper_model=model)
    report = deconstructor.deconstruct(share_url, transcribe=transcribe,
                                        analyze_frames=analyze_frames)
    if report.get('success'):
        return deconstructor.generate_template(report)
    return None


# ============================================================
# 测试入口
# ============================================================
if __name__ == '__main__':
    import sys
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    if len(sys.argv) < 2:
        print("用法: python deconstruct_v2.py <抖音分享链接> [选项]")
        print("  --transcribe: 转写音频")
        print("  --frames: 分析关键帧")
        print("  --model: Whisper模型 (base/small/medium/large)")
        print("  --template: 生成模板")
        sys.exit(1)
    
    share_url = sys.argv[1]
    transcribe = '--transcribe' in sys.argv
    analyze_frames = '--frames' in sys.argv
    template_mode = '--template' in sys.argv
    
    # 获取模型大小
    model = 'base'
    if '--model' in sys.argv:
        idx = sys.argv.index('--model')
        if idx + 1 < len(sys.argv):
            model = sys.argv[idx + 1]
    
    try:
        if template_mode:
            # 模板模式
            result = generate_template_v2(share_url, transcribe=transcribe,
                                          analyze_frames=analyze_frames, model=model)
            if result:
                print("\n" + "=" * 60)
                print("[TEMPLATE] 可复用模板")
                print("=" * 60)
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print("[X] 模板生成失败")
        else:
            # 报告模式
            report = deconstruct_video_v2(share_url, transcribe=transcribe,
                                          analyze_frames=analyze_frames, model=model)
            if report.get('success'):
                _print_report_v2(report)
            else:
                print(f"[X] 拆解失败: {report.get('error', '')}")
    except Exception as e:
        print(f"[X] 错误: {e}")
        import traceback
        traceback.print_exc()


def _print_report_v2(report: Dict):
    """格式化输出拆解报告（使用 ASCII 替代字符，避免 Windows GBK 编码报错）"""
    dims = report.get('dimensions', {})
    
    print(f"\n[VIDEO] 视频: {dims.get('video_meta', {}).get('title', '')[:60]}")
    print(f"[TIME] 时长: {dims.get('video_meta', {}).get('duration_sec', 0):.1f}s")
    print(f"[SCORE] 得分: {report.get('score', 0):.0f}/100")
    
    print(f"\n[AUTHOR] 作者: {dims.get('author_profile', {}).get('nickname', '')}")
    
    # 互动数据
    metrics = dims.get('engagement_metrics', {})
    print(f"\n[STATS] 互动数据:")
    print(f"  [LIKE] 点赞: {metrics.get('digg_count', 0):,}")
    print(f"  [COMM] 评论: {metrics.get('comment_count', 0):,}")
    print(f"  [SHAR] 分享: {metrics.get('share_count', 0):,}")
    print(f"  [SAVE] 收藏: {metrics.get('collect_count', 0):,}")
    print(f"  总互动: {metrics.get('total_interaction', 0):,}")
    
    # 内容结构
    content = dims.get('content_structure', {})
    print(f"\n[STRUCT] 内容结构:")
    print(f"  钩子: {content.get('hook_type', '')}")
    print(f"  正文: {content.get('body_structure', '')}")
    print(f"  CTA: {', '.join(content.get('cta_types', ['无']))}")
    print(f"  视觉: {content.get('visual_style', '')}")
    
    # 音频转写
    transcribe = dims.get('audio_transcription', {})
    if transcribe.get('success'):
        print(f"\n[TRANS] 配音转写:")
        print(f"  字数: {transcribe.get('word_count', 0)}")
        print(f"  时长: {transcribe.get('duration_sec', 0):.1f}s")
        print(f"  内容: {transcribe.get('transcribed_text', '')[:200]}...")
        print(f"  风格: {dims.get('audio_analysis', {}).get('voiceover_style', '')}")
    
    # 关键帧
    frames = dims.get('frame_analysis', {})
    if frames.get('success') and frames.get('frame_count', 0) > 0:
        print(f"\n[FRAME] 关键帧: {frames.get('frame_count', 0)} 帧提取成功")
    
    # 标签
    tags = dims.get('tag_cluster', {})
    print(f"\n[TAGS] 标签: {', '.join(tags.get('tags', []))}")
    print(f"[CAT] 分类: {tags.get('category', '')}")
    
    # 评论
    comments = dims.get('comment_sentiment', {})
    if comments.get('hot_comments'):
        print(f"\n[COMMENTS] 热门评论 ({comments.get('comment_count', 0)}条):")
        for c in comments['hot_comments'][:3]:
            print(f"  @{c['user']}: {c['text'][:50]} [{c['likes']}赞]")
    
    # 模板
    template = dims.get('reusable_template', {})
    if template.get('template_type'):
        print(f"\n[TEMPLATE] 可复用模板: {template['template_type']}")
        print(f"  适用场景: {', '.join(template.get('applicable_to', []))}")
        if template.get('suggestion'):
            print(f"  建议: {template['suggestion'][0]}")
