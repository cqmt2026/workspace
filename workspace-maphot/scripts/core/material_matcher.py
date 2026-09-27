# -*- coding: utf-8 -*-
"""
文案 → 视频素材 匹配模块

核心功能：
1. 维护视频素材索引库（记录已下载素材的关键词、时长、分辨率、来源）
2. 分析文案，提取每段的主题关键词
3. 根据关键词匹配合适的视频素材
4. 集成 Pixabay 素材搜索与下载
5. 生成"时间段 → 素材"的渲染清单

使用：
    matcher = MaterialMatcher()
    result = matcher.match_script(script_text, video_duration)
    # result: {
    #   'matches': [{'start': 0, 'end': 6, 'segment': '...', 'keywords': [...], 'material': {...}}],
    #   'coverage': 0.8,   # 素材覆盖比例
    #   'scheme': {...}    # 完整渲染方案
    # }
"""

import os
import re
import json
import time
import subprocess
import urllib.request
import urllib.parse
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'modules'))
try:
    from pixabay_fetcher import search_videos, download_video
except ImportError:
    search_videos = None
    download_video = None


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class MaterialMatcher:
    """文案 → 素材匹配器"""

    # 素材库索引路径
    MATERIAL_INDEX = os.path.join(BASE_DIR, 'data', 'materials', 'material_index.json')
    MATERIAL_DIR = os.path.join(BASE_DIR, 'data', 'videos', '素材')

    # ========== 主题关键词库 ==========
    # 每个主题类型匹配的关键词和对应的Pixabay搜索词
    TOPIC_MATERIAL_MAP = {
        # 贸易/经济
        'trade': {
            'keywords': ['贸易', '外贸', '进出口', '出口', '进口', '出口贸易', '对外贸易', '贸易伙伴',
                         '港口', '集装箱', '货轮', '码头', '物流', '航运', 'ship', 'container', 'port', 'cargo'],
            'pixabay_keywords': ['container ship', 'cargo port', 'container terminal', 'trade'],
            'materials': ['port_container', 'night_port', 'crane_port'],
            'desc': '贸易/港口素材',
        },
        # 经济/金融
        'economy': {
            'keywords': ['经济', 'GDP', '增长', '金融', '投资', '信贷', '市场', '股市', 'economy', 'finance', 'market'],
            'pixabay_keywords': ['city skyline', 'stock market', 'finance', 'money'],
            'materials': ['shanghai', 'city_buildings'],
            'desc': '经济/城市素材',
        },
        # 城市/中国
        'china_city': {
            'keywords': ['北京', '上海', '广州', '深圳', '成都', '重庆', '杭州', '城市', '一线城市',
                         'china', 'shanghai', 'beijing', 'city'],
            'pixabay_keywords': ['china city', 'shanghai skyline', 'beijing'],
            'materials': ['shanghai', 'city_buildings'],
            'desc': '中国城市素材',
        },
        # 历史/建设
        'history': {
            'keywords': ['历史', '过去', '当年', '曾经的', '变迁', '发展', '从', '到', '加入', '成立',
                         'history', 'development', 'grow'],
            'pixabay_keywords': ['construction', 'development', 'city aerial'],
            'materials': ['shanghai', 'crane_port'],
            'desc': '历史/建设素材',
        },
        # 工厂/制造业
        'manufacturing': {
            'keywords': ['制造', '工厂', '工业', '生产', '车企', '生产线', 'manufacturing', 'factory', 'industry'],
            'pixabay_keywords': ['factory', 'industrial', 'manufacturing'],
            'materials': ['factory', 'industrial_plant'],
            'desc': '工业/制造素材',
        },
        # 物流/运输
        'logistics': {
            'keywords': ['物流', '运输', '货运', '供应链', '铁路', '高铁', '物流园', 'logistics', 'transport'],
            'pixabay_keywords': ['logistics', 'freight train', 'transport'],
            'materials': ['port_container', 'crane_port'],
            'desc': '物流/运输素材',
        },
        # 粮食/农业
        'agriculture': {
            'keywords': ['农业', '粮食', '种植', '农民', '丰收', '农产品', '农业', 'agriculture', 'farm'],
            'pixabay_keywords': ['farm', 'agriculture', 'wheat field'],
            'materials': [],
            'desc': '农业素材',
        },
        # 人口/民生
        'people': {
            'keywords': ['人口', '居民', '百姓', '民生', '生活', '就业', '人民', 'people', 'population'],
            'pixabay_keywords': ['people city', 'crowd', 'community'],
            'materials': ['city_buildings'],
            'desc': '人口/民生素材',
        },
        # 天气/灾害
        'weather': {
            'keywords': ['天气', '台风', '暴雨', '洪水', '干旱', '高温', '寒潮', '地震', '灾害',
                         'storm', 'flood', 'rain', 'heat', 'typhoon', 'weather', 'disaster'],
            'pixabay_keywords': ['storm', 'flood', 'rain storm', 'typhoon', 'snow'],
            'materials': [],
            'desc': '天气/灾害素材',
        },
        # 美食/消费
        'food': {
            'keywords': ['美食', '消费', '餐饮', '火锅', '烧烤', '小吃', '餐厅', '饮食', 'eating', 'food', 'restaurant'],
            'pixabay_keywords': ['food market', 'cooking', 'restaurant', 'street food'],
            'materials': [],
            'desc': '美食/消费素材',
        },
        # 科技/互联网
        'tech': {
            'keywords': ['科技', '互联网', 'AI', '人工智能', '芯片', '5G', '科技', 'technology', 'internet', 'digital'],
            'pixabay_keywords': ['technology', 'computers', 'data center', 'robot', 'digital'],
            'materials': [],
            'desc': '科技/互联网素材',
        },
        # 娱乐/文化
        'entertainment': {
            'keywords': ['电影', '明星', '演唱会', '综艺', '娱乐', '文化', 'movie', 'entertainment', 'concert'],
            'pixabay_keywords': ['concert', 'movie theater', 'celebrity', 'festival'],
            'materials': [],
            'desc': '娱乐/文化素材',
        },
        # 体育/赛事
        'sports': {
            'keywords': ['体育', '足球', '篮球', '奥运', '世界杯', '比赛', '运动员', '运动会', '亚运会', '中国队', '金牌', '冠军', '选手', '奖牌',
                         'sports', 'football', 'basketball', 'olympics', 'gold medal', 'athlete'],
            'pixabay_keywords': ['stadium', 'soccer', 'basketball', 'olympics', 'sports', 'athletes'],
            'materials': [],
            'desc': '体育/赛事素材',
        },
        # 交通/出行
        'transport': {
            'keywords': ['交通', '高铁', '飞机', '地铁', '汽车', '高速', '出行', '铁路', '航空', '公路', '运输',
                         'traffic', 'transport', 'highway', 'airplane', 'subway', 'train', 'flight'],
            'pixabay_keywords': ['highway', 'airplane', 'train', 'traffic', 'subway', 'high speed train'],
            'materials': ['port_container', 'crane_port'],
            'desc': '交通/出行素材',
        },
        # 能源/环境
        'energy': {
            'keywords': ['能源', '石油', '煤炭', '新能源', '太阳能', '风电', '环保', '环境', 'energy', 'wind solar'],
            'pixabay_keywords': ['wind turbine', 'solar panel', 'oil refinery', 'power plant'],
            'materials': [],
            'desc': '能源/环境素材',
        },
        # 军事/国防
        'military': {
            'keywords': ['军事', '国防', '军舰', '飞机', '武器', '演习', 'military', 'warship', 'army'],
            'pixabay_keywords': ['military', 'warship', 'aircraft carrier', 'soldiers'],
            'materials': [],
            'desc': '军事/国防素材',
        },
        # 房地产/建筑
        'real_estate': {
            'keywords': ['房产', '房价', '建筑', '楼盘', '地产', '房屋', 'real estate', 'building', 'house'],
            'pixabay_keywords': ['building', 'construction site', 'skyscraper', 'architecture'],
            'materials': ['shanghai'],
            'desc': '房地产/建筑素材',
        },
        # 教育/医疗
        'education': {
            'keywords': ['教育', '大学', '学校', '高考', '考研', '医院', '医疗', 'health', 'education', 'university'],
            'pixabay_keywords': ['university campus', 'hospital', 'students', 'classroom'],
            'materials': [],
            'desc': '教育/医疗素材',
        },
        # 旅游/风景
        'travel': {
            'keywords': ['旅游', '景点', '风景', '景区', '旅行', 'travel', 'tourism', 'landscape', 'scenic'],
            'pixabay_keywords': ['landscape', 'mountain', 'travel', 'nature', 'park'],
            'materials': [],
            'desc': '旅游/风景素材',
        },
        # 金融/股市
        'finance': {
            'keywords': ['股市', '基金', '银行', '证券', '金融', '投资', '理财', 'stock', 'bank', 'finance', 'investment'],
            'pixabay_keywords': ['stock market', 'bank', 'money', 'trading', 'finance'],
            'materials': ['shanghai'],
            'desc': '金融/股市素材',
        },
        # 电商/直播
        'ecommerce': {
            'keywords': ['电商', '直播', '带货', '网购', '拼多多', '淘宝', '电商', 'ecommerce', 'livestream', 'shopping'],
            'pixabay_keywords': ['online shopping', 'delivery', 'warehouse', 'package'],
            'materials': ['port_container', 'crane_port'],
            'desc': '电商/直播素材',
        },
    }

    def __init__(self, material_dir=None, index_path=None):
        self.material_dir = material_dir or self.MATERIAL_DIR
        self.index_path = index_path or self.MATERIAL_INDEX
        self.index = self._load_index()

    def _load_index(self):
        """加载素材索引库"""
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {'materials': [], 'updated_at': None}

    def _save_index(self):
        """保存素材索引库"""
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        with open(self.index_path, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, ensure_ascii=False, indent=2)

    def register_material(self, filename, keywords, duration=0, source='local',
                          topic_type=None, desc=''):
        """
        将本地素材注册到索引库
        
        Args:
            filename: 素材文件名（不含路径）
            keywords: 关键词列表
            duration: 素材时长（秒）
            source: 来源（local/pixabay）
            topic_type: 主题类型
            desc: 描述
        """
        # 检查是否已存在
        for m in self.index['materials']:
            if m.get('filename') == filename:
                m.update({
                    'filename': filename,
                    'keywords': keywords,
                    'duration': duration,
                    'source': source,
                    'topic_type': topic_type,
                    'desc': desc,
                    'path': os.path.join('data', 'videos', '素材', filename),
                })
                self._save_index()
                return m
        
        material = {
            'id': 'mat_%d' % int(time.time()),
            'filename': filename,
            'keywords': keywords,
            'duration': duration,
            'source': source,
            'topic_type': topic_type,
            'desc': desc,
            'path': os.path.join('data', 'videos', '素材', filename),
        }
        self.index['materials'].append(material)
        self.index['updated_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        self._save_index()
        return material

    def get_material_duration(self, path):
        """获取素材时长"""
        try:
            r = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                 '-of', 'csv=p=0', path],
                capture_output=True, text=True, timeout=10,
                encoding='utf-8', errors='replace')
            if r.returncode == 0 and r.stdout.strip():
                return float(r.stdout.strip())
        except Exception:
            pass
        return 0

    def extract_segments(self, script_text):
        """
        将文案按段落拆分为带主题标签的片段
        
        Returns:
            list of dict: [{'text': '...', 'keywords': [...], 'topic': 'trade'}]
        """
        if not script_text:
            return []
        
        # 按换行或句号拆分
        raw_segments = [s.strip() for s in re.split(r'[\n]+', script_text) if s.strip()]
        if len(raw_segments) <= 1:
            raw_segments = [s.strip() for s in re.split(r'[。!?！？]', script_text) if s.strip()]
        
        segments = []
        for text in raw_segments:
            keywords, topic = self._analyze_keywords(text)
            segments.append({
                'text': text,
                'keywords': keywords,
                'topic': topic,
            })
        
        return segments

    def _analyze_keywords(self, text):
        """
        分析一段文案，提取主题关键词和主题类型
        
        Returns: (keywords, topic_type)
        """
        keywords = []
        topic_scores = {}
        
        for topic_type, config in self.TOPIC_MATERIAL_MAP.items():
            score = 0
            for kw in config['keywords']:
                # 关键词出现在文本中
                if kw.lower() in text.lower():
                    score += 1
                    if kw not in keywords:
                        keywords.append(kw)
            if score > 0:
                topic_scores[topic_type] = score
        
        # 选择得分最高的主题（平局时优先更具体的主题）
        best_topic = None
        best_score = 0
        for topic, score in topic_scores.items():
            if score > best_score:
                best_topic = topic
                best_score = score
            elif score == best_score and score > 0:
                # 平局：优先匹配关键词更多的主题（更具体）
                if len([kw for kw in self.TOPIC_MATERIAL_MAP[topic]['keywords'] if kw.lower() in text.lower()]) > len([kw for kw in self.TOPIC_MATERIAL_MAP[best_topic]['keywords'] if kw.lower() in text.lower()]):
                    best_topic = topic
        
        # 如果没有匹配主题，返回通用
        if best_topic is None:
            best_topic = 'economy'
            # 补充通用关键词
            for word in ['中国', '全球', '世界', '市场', '贸易', '增长']:
                if word in text:
                    keywords.append(word)
        
        return keywords, best_topic

    def match_material(self, topic_type, keywords=None, need_duration=6):
        """
        根据主题和关键词匹配素材
        
        Args:
            topic_type: 主题类型
            keywords: 额外关键词
            need_duration: 需要的时长（秒）
        
        Returns:
            dict or None: 匹配到的素材信息
        """
        # 获取该主题对应的素材
        config = self.TOPIC_MATERIAL_MAP.get(topic_type, {})
        preferred = config.get('materials', [])
        
        # 优先匹配特定素材
        for mat_name in preferred:
            for m in self.index['materials']:
                if m.get('filename', '').replace('.mp4', '') == mat_name:
                    return m
        
        # 再按关键词匹配
        keyword_set = set(keywords or [])
        best_match = None
        best_score = 0
        for m in self.index['materials']:
            mat_keywords = set(m.get('keywords', []))
            score = len(keyword_set & mat_keywords)
            if score > best_score:
                best_score = score
                best_match = m
        
        if best_match:
            return best_match
        
        return None

    async def search_pixabay(self, query, count=3):
        """搜索Pixabay素材（集成真实API）"""
        if search_videos is None:
            return {'query': query, 'error': 'pixabay_fetcher不可用'}
        try:
            results = search_videos(query, per_page=count)
            return {'query': query, 'results': results, 'count': len(results)}
        except Exception as e:
            return {'query': query, 'error': str(e)}

    def download_by_keywords(self, keywords, output_dir=None, max_results=3):
        """
        根据关键词搜索并下载Pixabay素材
        
        Returns:
            list of dict: [{filename, path, query, duration}]
        """
        if search_videos is None:
            logger = __import__('logging').getLogger(__name__)
            logger.warning("Pixabay fetcher不可用，跳过下载")
            return []
        
        # 尝试用最佳匹配词搜索
        for kw in keywords[:3]:
            # 中文关键词转英文（简单映射）
            query_en = self._chinese_to_english(kw)
            if not query_en:
                continue
            results = search_videos(query_en, per_page=max_results)
            if not results:
                continue
            
            downloaded = []
            for r in results[:max_results]:
                path = download_video(r, output_dir)
                if path:
                    fname = os.path.basename(path)
                    downloaded.append({
                        'filename': fname,
                        'path': path,
                        'query': query_en,
                        'duration': r.get('duration', 0),
                        'size': r.get('width', 0),
                    })
                    # 注册到索引
                    self.register_material(fname, keywords, duration=r.get('duration',0),
                                         source='pixabay', topic_type=self._guess_topic(keywords),
                                         desc=r.get('tags', '')[:50])
            if downloaded:
                return downloaded
        
        return []

    def _chinese_to_english(self, cn_kw):
        """中英文关键词映射"""
        mapping = {
            # 贸易物流
            '贸易': 'trade', '外贸': 'foreign trade', '进出口': 'import export',
            '港口': 'port', '集装箱': 'container ship', '货轮': 'cargo ship',
            '码头': 'harbor', '物流': 'logistics', '航运': 'shipping', '货运': 'freight',
            # 经济金融
            '经济': 'economy', '金融': 'finance', '股市': 'stock market',
            '银行': 'bank', '投资': 'investment', '市场': 'market',
            'GDP': 'economy', '增长': 'growth', '信贷': 'credit',
            # 城市中国
            '上海': 'shanghai', '北京': 'beijing', '广州': 'guangzhou',
            '深圳': 'shenzhen', '成都': 'chengdu', '重庆': 'chongqing',
            '杭州': 'hangzhou', '城市': 'city skyline', '中国': 'china city',
            '浦东': 'shanghai skyline', '一线城市': 'china city',
            # 建设历史
            '建设': 'construction', '发展': 'development', '历史': 'history',
            '变迁': 'transformation', '加入': 'join', '成立': 'established',
            # 工业制造
            '工厂': 'factory', '制造': 'manufacturing', '工业': 'industrial',
            '生产': 'production', '生产线': 'assembly line', '车企': 'car factory',
            # 农业粮食
            '农业': 'agriculture', '粮食': 'wheat field', '农场': 'farm',
            '种植': 'farming', '丰收': 'harvest', '农产品': 'agricultural products',
            # 天气灾害
            '天气': 'weather', '台风': 'typhoon', '暴雨': 'storm',
            '洪水': 'flood', '地震': 'earthquake', '高温': 'heat wave',
            '寒潮': 'cold wave', '干旱': 'drought', '灾害': 'disaster',
            # 美食消费
            '美食': 'food', '消费': 'shopping', '餐饮': 'restaurant',
            '火锅': 'hot pot', '烧烤': 'barbecue', '小吃': 'street food',
            # 科技互联网
            '科技': 'technology', '互联网': 'internet', 'AI': 'artificial intelligence',
            '人工智能': 'AI robot', '芯片': 'microchip', '5G': '5G technology',
            '数据': 'data center', '数字': 'digital',
            # 娱乐文化
            '电影': 'movie', '明星': 'celebrity', '演唱会': 'concert',
            '综艺': 'variety show', '娱乐': 'entertainment', '文化': 'culture',
            # 体育赛事
            '体育': 'sports', '足球': 'soccer', '篮球': 'basketball',
            '奥运': 'olympics', '世界杯': 'world cup', '比赛': 'stadium',
            '运动员': 'athlete', '冠军': 'champion',
            # 交通出行
            '高铁': 'high speed train', '飞机': 'airplane', '地铁': 'subway',
            '高速': 'highway', '交通': 'traffic', '汽车': 'car', '火车': 'train',
            # 能源环境
            '能源': 'energy', '石油': 'oil refinery', '风电': 'wind turbine',
            '太阳能': 'solar panel', '环保': 'environment', '污染': 'pollution',
            # 民生人口
            '人口': 'people city', '居民': 'community', '就业': 'employment',
            '民生': 'living', '生活': 'lifestyle', '百姓': 'citizens',
            # 房地产建筑
            '房产': 'real estate', '房价': 'house price', '建筑': 'building',
            '楼盘': 'residential', '房屋': 'house',
            # 教育医疗
            '教育': 'education', '大学': 'university', '学校': 'school',
            '高考': 'students', '考研': 'exam', '医院': 'hospital', '医疗': 'healthcare',
            # 旅游风景
            '旅游': 'travel', '景点': 'landscape', '风景': 'nature',
            '景区': 'tourist attraction', '旅行': 'travel',
            # 电商直播
            '电商': 'ecommerce', '直播': 'livestream', '网购': 'online shopping',
            '带货': 'shopping live', '拼多多': 'ecommerce', '淘宝': 'shopping',
            # 军事国防
            '军事': 'military', '国防': 'defense', '军舰': 'warship',
            '演习': 'military exercise', '武器': 'weapons',
            # 通用
            '全球': 'global', '世界': 'world', '国家': 'country', '城市': 'city',
        }
        for cn, en in mapping.items():
            if cn in cn_kw:
                return en
        return cn_kw

    def _guess_topic(self, keywords):
        """从关键词猜测主题类型"""
        for kw in keywords:
            for topic, config in self.TOPIC_MATERIAL_MAP.items():
                if kw in str(config['keywords']):
                    return topic
        return 'economy'

    def auto_download_missing(self, result, output_dir=None):
        """
        自动下载缺失的素材
        
        Args:
            result: build_render_scheme 返回的结果
            output_dir: 输出目录，默认 data/videos/素材/
        """
        if download_video is None:
            return []
        
        if output_dir is None:
            output_dir = self.MATERIAL_DIR
        os.makedirs(output_dir, exist_ok=True)
        
        downloaded = []
        for m in result.get('matches', []):
            if m.get('material'):
                continue  # 已有素材，跳过
            keywords = m.get('keywords', [])
            if not keywords:
                continue
            # 搜索并下载
            for kw in keywords[:3]:
                en_kw = self._chinese_to_english(kw)
                if not en_kw:
                    continue
                results = search_videos(en_kw, per_page=2)
                if not results:
                    continue
                for r in results[:2]:
                    path = download_video(r, output_dir)
                    if path:
                        fname = os.path.basename(path)
                        # 注册到索引
                        self.register_material(fname, keywords,
                                              duration=r.get('duration',0),
                                              source='pixabay',
                                              topic_type=m.get('topic'),
                                              desc=r.get('tags','')[:50])
                        downloaded.append({'filename': fname, 'path': path, 'segment': m})
                        break  # 一个关键词找到即可
                if downloaded and downloaded[-1]['segment'] == m:
                    break
        
        return downloaded

    def build_render_scheme(self, script_text, video_duration=None,
                            material_durations=None):
        """
        构建完整渲染方案：把文案片段映射到时间段和素材
        
        Args:
            script_text: 完整文案
            video_duration: 视频总时长（秒），None则估算
            material_durations: dict，素材名→时长（秒）的映射
        
        Returns:
            dict: 完整渲染方案
        """
        segments = self.extract_segments(script_text)
        if not segments:
            return {'matches': [], 'coverage': 0, 'scheme': None}
        
        # 估算总时长（按字数，每秒5-6个字）
        if video_duration is None:
            char_count = len(script_text)
            video_duration = max(20, int(char_count / 5.5))
        
        # 计算每段时长（按字数比例）
        total_chars = sum(len(s['text']) for s in segments)
        seg_durations = []
        for s in segments:
            dur = max(3, int(len(s['text']) / total_chars * video_duration))
            seg_durations.append(dur)
        
        # 时间轴累加
        matches = []
        current_time = 0
        for i, seg in enumerate(segments):
            dur = seg_durations[i]
            material = self.match_material(seg['topic'], seg['keywords'])
            
            match = {
                'index': i,
                'start': current_time,
                'end': current_time + dur,
                'duration': dur,
                'text': seg['text'],
                'keywords': seg['keywords'],
                'topic': seg['topic'],
                'material': material,
            }
            matches.append(match)
            current_time += dur
        
        # 计算覆盖比例（有素材的段占比）
        covered = sum(1 for m in matches if m['material'])
        coverage = covered / max(1, len(matches))
        
        scheme = {
            'video_duration': video_duration,
            'match_count': len(matches),
            'covered_count': covered,
            'coverage': coverage,
            'timeline': matches,
        }
        
        return {
            'matches': matches,
            'coverage': coverage,
            'scheme': scheme,
        }
    
    def full_pipeline(self, script_text, video_duration=None, auto_download=True):
        """
        完整管线：匹配 + 下载缺失素材
        
        Returns:
            dict: 完整渲染方案
        """
        result = self.build_render_scheme(script_text, video_duration)
        
        if auto_download:
            missing = [m for m in result['matches'] if not m['material']]
            if missing:
                logger = __import__('logging').getLogger(__name__)
                logger.info("下载 %d 个缺失素材..." % len(missing))
                downloaded = self.auto_download_missing(result)
                result['downloaded'] = downloaded
                # 重新匹配（下载后可能更新了索引）
                result = self.build_render_scheme(script_text, video_duration)
                result['downloaded'] = downloaded
        
        return result

    def format_scheme(self, result):
        """生成人类可读的渲染方案"""
        lines = []
        lines.append('文案 → 素材 匹配方案')
        lines.append('=' * 60)
        lines.append('视频总时长: %d秒 | 素材覆盖: %.0f%%' % (
            result['scheme']['video_duration'], result['coverage'] * 100))
        lines.append('-' * 60)
        
        for m in result['matches']:
            time_str = '%d-%ds' % (m['start'], m['end'])
            material_str = m['material']['filename'] if m['material'] else '（无素材，用动画/地图）'
            topic_names = {
                'trade': '贸易港口', 'economy': '经济城市', 'china_city': '中国城市',
                'history': '历史建设', 'manufacturing': '工业制造', 'logistics': '物流运输',
                'agriculture': '农业', 'people': '人口民生', 'economy': '经济',
            }
            topic_name = topic_names.get(m['topic'], m['topic'])
            lines.append('[%s] 主题:%s | %s' % (time_str, topic_name, material_str))
            lines.append('    "%s..."' % m['text'][:50])
        
        lines.append('-' * 60)
        lines.append('推荐素材来源:')
        for m in result['matches']:
            if not m['material']:
                lines.append('  - %d-%ds: 需搜索 "%s"' % (
                    m['start'], m['end'], m['keywords'][0] if m['keywords'] else m['topic']))
        
        return '\n'.join(lines)


# ========== 便捷函数 ==========

def match_script(script_text, video_duration=None):
    """快速入口：匹配文案到素材"""
    matcher = MaterialMatcher()
    return matcher.build_render_scheme(script_text, video_duration)


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    demo_script = (
        "你知道吗？中国的贸易朋友圈已经扩张到了160多个国家和地区！\n"
        "最新数据显示，中国已成为全球160多个国家和地区的主要贸易伙伴，比2020年增加了20多个。\n"
        "其中，RCEP成员国是中国贸易的核心圈。15个国家，去年进出口额达到12.6万亿元。\n"
        "除了RCEP，中国还和24个国家签署了自贸协定，涉及31个国家和地区。\n"
        "金砖国家扩容后，中国贸易朋友圈再添新成员。\n"
        "从2001年加入WTO到如今，中国从一个贸易大国成长为全球贸易第一大国。\n"
        "你怎么看中国贸易朋友圈的扩张？评论区告诉我！"
    )
    
    matcher = MaterialMatcher()
    
    # 注册现有素材
    matcher.register_material('port_container.mp4',
                              ['集装箱', '港口', '贸易', '货轮', '码头'],
                              source='pixabay', topic_type='trade', desc='集装箱港口')
    matcher.register_material('night_port.mp4',
                              ['码头', '港口', '货轮', '夜色', '集装箱'],
                              source='pixabay', topic_type='trade', desc='夜间码头货轮')
    matcher.register_material('shanghai.mp4',
                              ['上海', '浦东', '城市', '天际线', '经济'],
                              source='pixabay', topic_type='china_city', desc='上海浦东天际线')
    
    print("素材索引库:")
    for m in matcher.index['materials']:
        print('  - %s: %s' % (m['filename'], m['desc']))
    
    print()
    result = matcher.build_render_scheme(demo_script, video_duration=55)
    print(matcher.format_scheme(result))
