#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
动态选题引擎 V2.0
基于实时热点数据生成候选选题（替代写死的topic_recommender）

核心改进：
- 选题从热点数据动态生成，不再写死
- 接入热点采集器的真实数据
- 竞品去重（基于历史已发文章）
- 历史表现反馈（哪类选题效果好）
- 输出候选选题供老板选择

作者：小智
版本：V2.0
创建时间：2026-03-25
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
import sys
from typing import Dict, List, Any, Optional
from collections import Counter

sys.path.append(str(Path(__file__).parent))
from logger import logger


# 房地产相关关键词库
REALESTATE_KEYWORDS = {
    'policy': ['公积金', '房贷', '限购', '限售', '落户', '税收', '契税', '利率', 
               '首付', '贷款', '住建', '住房', '保障房', '公租房', '共有产权'],
    'market': ['房价', '成交', '涨价', '降价', '库存', '去化', '均价', '地王',
               '土地', '土拍', '溢价', '流拍', '开盘', '摇号', '认购'],
    'city': ['重庆', '两江新区', '科学城', '高新区', '渝北', '江北', '南岸',
             '沙坪坝', '九龙坡', '巴南', '北碚', '渝中', '大渡口', '璧山',
             '照母山', '中央公园', '礼嘉', '悦来', '蔡家', '水土'],
    'life': ['装修', '交房', '验房', '维权', '物业', '学区', '地铁', '配套',
             '精装', '毛坯', '二手房', '新房', '楼盘', '小区', '户型'],
    'event': ['春交会', '房交会', '两会', '金九银十', '小阳春', '年底冲刺']
}

# 选题类型模板（用于把热点转化为选题角度）- V2.1 增加多样性
TOPIC_ANGLES = {
    'policy': [
        '{keyword}新政解读：对{city}购房者意味着什么',
        '{keyword}政策落地，{city}这些人受影响最大',
        '{keyword}调整后，{city}买房能省多少钱？',
        '一文读懂{keyword}新规：{city}购房者必看',
        '{keyword}政策出台，{city}房东要坐不住了',
        '深夜解读：{keyword}背后的 3 个信号',
    ],
    'market': [
        '{city}{keyword}数据出炉：哪个区最值得关注？',
        '{city}楼市{keyword}变化，释放了什么信号？',
        '{keyword}背后的真相：{city}楼市到底怎么了？',
        '从{keyword}看{city}楼市走向：3 个关键判断',
        '{city}{keyword}数据曝光，业主群炸锅了',
        '深夜实探：{city}{keyword}的真实情况',
    ],
    'hotspot': [
        '{event}来了！{city}这些楼盘值得重点关注',
        '{event}深度解读：对{city}楼市的 3 大影响',
        '{event}之后，{city}买房要注意这几点',
        '{event}现场实拍：{city}人挤人，真相是...',
        '{event}第一天，{city}销售说漏了嘴',
    ],
    'guide': [
        '{city}购房避坑指南：{keyword}你一定要知道',
        '在{city}买房，{keyword}这件事千万别忽略',
        '{keyword}全攻略：{city}购房者实用手册',
        '{city}买房血泪史：这 5 个坑我替你踩了',
        '中介不会说的{keyword}秘密，今天曝光',
    ],
    'opinion': [
        '{city}房价到底{keyword}了没？说 3 个不受欢迎的真话',
        '为什么我劝你别在{area}买房？从业者的心里话',
        '{keyword}争议：{city}楼市的真实情况是这样的',
        '{city}楼市 3 大怪象，第 2 个最坑人',
        '对不起，这次我看空{city}楼市',
    ],
    'case': [
        '{city}业主{keyword}实录：从买入到出手的全过程',
        '我在{city}买房的 3 个教训，希望你别犯',
        '{area}楼盘{keyword}案例：买对赚 50 万，买错亏 30 万',
    ]
}


class TopicEngineV2:
    """
    动态选题引擎
    
    工作流程：
    1. 读取热点采集数据
    2. 过滤出房地产相关热点
    3. 提取关键词和话题
    4. 匹配选题角度模板
    5. 评分排序
    6. 与历史选题去重
    7. 输出候选选题
    """
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).parent.parent
        self.pipeline_dir = self.base_dir / 'pipeline_data'
        self.hotspots_dir = self.pipeline_dir / 'hotspots'
        self.candidates_dir = self.pipeline_dir / 'candidates'
        self.articles_dir = self.base_dir / 'articles'
        self.history_dir = self.base_dir / 'topic_evaluations'
        
        # 确保目录存在
        for d in [self.pipeline_dir, self.hotspots_dir, self.candidates_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        # 加载历史数据
        self.published_titles = self._load_published_titles()
        self.history_performance = self._load_history_performance()
        
        logger.info(f"选题引擎V2初始化 | 已发文章: {len(self.published_titles)} | 历史记录: {len(self.history_performance)}")
    
    def generate_candidates(self, hotspot_data: Optional[List[Dict]] = None, count: int = 8) -> List[Dict]:
        """
        生成候选选题
        
        Args:
            hotspot_data: 热点数据（None 则从文件读取最新）
            count: 生成数量
        
        Returns:
            候选选题列表
        """
        # 1. 获取热点数据
        if hotspot_data is None:
            hotspot_data = self._load_latest_hotspots()
        
        if not hotspot_data:
            logger.warning("无热点数据，使用常青选题兜底")
            return self._get_evergreen_topics()[:count]
        
        logger.info(f"输入热点：{len(hotspot_data)} 条")
        
        # 2. 过滤房地产相关
        re_hotspots = self._filter_realestate(hotspot_data)
        logger.info(f"房地产相关：{len(re_hotspots)} 条")
        
        # 3. 生成选题候选
        candidates = []
        for hotspot in re_hotspots:
            topics = self._expand_to_topics(hotspot)
            candidates.extend(topics)
        
        # 4. 如果候选不够，补充常青选题
        if len(candidates) < 5:
            evergreen = self._get_evergreen_topics()
            for eg in evergreen[:8 - len(candidates)]:
                candidates.append({
                    'title': eg.get('title', '重庆购房指南'),
                    'type': 'guide',
                    'source_hotspot': '常青选题',
                    'keywords': eg.get('matched_keywords', []),
                    'hot_level': eg.get('hot_level', 'low'),
                    'urgency': 'low',
                    'created_at': datetime.now().isoformat(),
                    'is_evergreen': True
                })
            logger.info(f"补充常青选题，总计：{len(candidates)} 条")
        
        # 5. 评分
        for topic in candidates:
            topic['score'] = self._score_topic(topic)
        
        # 6. 去重（与已发文章）
        candidates = self._deduplicate(candidates)
        
        # 7. 排序 + 截取
        candidates.sort(key=lambda x: x['score'], reverse=True)
        result = candidates[:count]
        
        # 8. 保存
        self._save_candidates(result)
        
        logger.info(f"生成候选选题：{len(result)} 个")
        return result
    def _load_latest_hotspots(self) -> List[Dict]:
        """加载最新的热点数据"""
        # 优先从pipeline_data/hotspots/读取
        hotspot_files = sorted(self.hotspots_dir.glob('*.json'), reverse=True)
        if hotspot_files:
            try:
                with open(hotspot_files[0], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    return data.get('hotspots', data.get('items', []))
            except Exception as e:
                logger.error(f"读取热点文件失败: {e}")
        
        # 兜底：从auto_hotspots读取
        auto_dir = self.base_dir / 'auto_hotspots'
        if auto_dir.exists():
            auto_files = sorted(auto_dir.glob('*.json'), reverse=True)
            if auto_files:
                try:
                    with open(auto_files[0], 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict):
                        return data.get('hotspots', data.get('items', []))
                except Exception as e:
                    logger.error(f"读取auto_hotspots失败: {e}")
        
        return []
    
    def _filter_realestate(self, hotspots: List[Dict]) -> List[Dict]:
        """过滤出房地产相关热点"""
        all_keywords = []
        for category in REALESTATE_KEYWORDS.values():
            all_keywords.extend(category)
        
        result = []
        for item in hotspots:
            title = item.get('title', '') + item.get('description', '') + item.get('content', '')
            # 计算相关度
            matched_keywords = [kw for kw in all_keywords if kw in title]
            if matched_keywords:
                item['matched_keywords'] = matched_keywords
                item['relevance'] = len(matched_keywords)
                result.append(item)
        
        # 按相关度排序
        result.sort(key=lambda x: x.get('relevance', 0), reverse=True)
        return result
    
    def _expand_to_topics(self, hotspot: Dict) -> List[Dict]:
        """将一条热点扩展为多个选题角度"""
        topics = []
        title = hotspot.get('title', '')
        matched_kws = hotspot.get('matched_keywords', [])
        
        # 判断选题类型
        topic_type = self._classify_hotspot(matched_kws)
        
        # 获取对应角度模板
        angles = TOPIC_ANGLES.get(topic_type, TOPIC_ANGLES['guide'])
        
        # 提取关键要素
        city = '重庆'
        for kw in matched_kws:
            if kw in REALESTATE_KEYWORDS['city']:
                city = kw
                break
        
        keyword = matched_kws[0] if matched_kws else '房价'
        area = ''
        for kw in matched_kws:
            if kw in REALESTATE_KEYWORDS['city'][3:]:  # 具体区域
                area = kw
                break
        
        # 生成选题
        for angle in angles[:2]:  # 每条热点最多2个角度
            try:
                topic_title = angle.format(
                    keyword=keyword, city=city, event=title[:10], area=area or city
                )
            except (KeyError, IndexError):
                topic_title = f"{city}{keyword}最新动态解读"
            
            topics.append({
                'title': topic_title,
                'type': topic_type,
                'source_hotspot': title,
                'keywords': matched_kws[:5],
                'hot_level': hotspot.get('hot_level', self._estimate_hot_level(hotspot)),
                'urgency': self._estimate_urgency(hotspot),
                'created_at': datetime.now().isoformat()
            })
        
        return topics
    
    def _classify_hotspot(self, keywords: List[str]) -> str:
        """根据关键词分类选题类型"""
        type_scores = {'policy': 0, 'market': 0, 'hotspot': 0, 'guide': 0, 'opinion': 0}
        
        for kw in keywords:
            if kw in REALESTATE_KEYWORDS['policy']:
                type_scores['policy'] += 2
            if kw in REALESTATE_KEYWORDS['market']:
                type_scores['market'] += 2
            if kw in REALESTATE_KEYWORDS['event']:
                type_scores['hotspot'] += 3
            if kw in REALESTATE_KEYWORDS['life']:
                type_scores['guide'] += 1
        
        # 返回得分最高的类型
        best_type = max(type_scores, key=type_scores.get)
        if type_scores[best_type] == 0:
            return 'guide'  # 默认
        return best_type
    
    def _estimate_hot_level(self, hotspot: Dict) -> str:
        """估算热度等级"""
        hot_value = hotspot.get('hot', hotspot.get('heat', hotspot.get('score', 0)))
        try:
            hot_value = int(hot_value)
        except (ValueError, TypeError):
            return 'medium'
        
        if hot_value > 1000000:
            return 'high'
        elif hot_value > 100000:
            return 'medium'
        else:
            return 'low'
    
    def _estimate_urgency(self, hotspot: Dict) -> str:
        """估算时效性"""
        title = hotspot.get('title', '')
        urgent_words = ['刚刚', '突发', '重磅', '今天', '最新', '紧急', '速看']
        if any(w in title for w in urgent_words):
            return 'high'
        
        time_words = ['本周', '近日', '最近', '即将']
        if any(w in title for w in time_words):
            return 'medium'
        
        return 'low'
    
    def _score_topic(self, topic: Dict) -> int:
        """选题综合评分（0-100）"""
        score = 0
        
        # 热度（35分）
        hot_map = {'high': 35, 'medium': 22, 'low': 10}
        score += hot_map.get(topic.get('hot_level', 'low'), 10)
        
        # 时效性（25分）
        urgency_map = {'high': 25, 'medium': 16, 'low': 8}
        score += urgency_map.get(topic.get('urgency', 'low'), 8)
        
        # 关键词丰富度（15分）
        kw_count = len(topic.get('keywords', []))
        score += min(15, kw_count * 4)
        
        # 选题类型加成（15分）——政策和热点类更容易爆
        type_bonus = {'policy': 15, 'hotspot': 13, 'market': 11, 'opinion': 10, 'guide': 8}
        score += type_bonus.get(topic.get('type', 'guide'), 8)
        
        # 历史表现反馈（10分）
        score += self._history_bonus(topic)
        
        return min(100, score)
    
    def _history_bonus(self, topic: Dict) -> int:
        """基于历史表现给分"""
        topic_type = topic.get('type', '')
        
        # 统计该类型的历史平均表现
        type_scores = [h.get('score', 0) for h in self.history_performance 
                       if h.get('type') == topic_type]
        
        if not type_scores:
            return 5  # 无历史数据给中等分
        
        avg = sum(type_scores) / len(type_scores)
        if avg >= 90:
            return 10
        elif avg >= 80:
            return 7
        elif avg >= 70:
            return 5
        return 3
    
    def _deduplicate(self, candidates: List[Dict]) -> List[Dict]:
        """与已发文章去重"""
        result = []
        for topic in candidates:
            title = topic['title']
            # 检查标题相似度（简单版：关键词重叠>60%则认为重复）
            is_dup = False
            title_words = set(re.findall(r'[\u4e00-\u9fff]+', title))
            
            for published in self.published_titles:
                pub_words = set(re.findall(r'[\u4e00-\u9fff]+', published))
                if not title_words or not pub_words:
                    continue
                overlap = len(title_words & pub_words) / max(len(title_words), 1)
                if overlap > 0.6:
                    is_dup = True
                    logger.debug(f"去重: {title} ≈ {published}")
                    break
            
            if not is_dup:
                result.append(topic)
        
        logger.info(f"去重: {len(candidates)} → {len(result)}")
        return result
    
    def _load_published_titles(self) -> List[str]:
        """加载已发布文章标题"""
        titles = []
        if self.articles_dir.exists():
            for f in self.articles_dir.glob('*.md'):
                titles.append(f.stem.replace('_', ' '))
        return titles
    
    def _load_history_performance(self) -> List[Dict]:
        """加载历史选题表现"""
        history = []
        eval_file = self.history_dir / 'evaluations.jsonl'
        if eval_file.exists():
            try:
                with open(eval_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            history.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
            except Exception:
                pass
        return history
    
    def _get_evergreen_topics(self) -> List[Dict]:
        """常青选题（兜底用）"""
        now = datetime.now()
        month = now.month
        
        # 根据月份生成时效性常青选题
        seasonal = {
            1: ['年底冲刺', '开年行情'],
            2: ['春节返乡置业', '开年政策'],
            3: ['小阳春', '两会政策', '春交会'],
            4: ['春交会', '学区房'],
            5: ['五一看房', '年中总结'],
            6: ['年中盘点', '暑期置业'],
            7: ['年中数据', '下半年预判'],
            8: ['金九预热', '下半年走势'],
            9: ['金九银十', '开盘季'],
            10: ['金九银十收官', '四季度展望'],
            11: ['年终冲刺', '年度总结'],
            12: ['年终盘点', '来年展望']
        }
        
        events = seasonal.get(month, ['购房指南'])
        
        topics = []
        for event in events:
            topics.append({
                'title': f'重庆{event}',
                'description': f'{now.year}年{month}月{event}相关话题',
                'matched_keywords': [event, '重庆'],
                'relevance': 2,
                'hot_level': 'medium',
                'is_evergreen': True
            })
        
        # 永久常青
        evergreen_base = [
            {'title': '重庆买房避坑', 'matched_keywords': ['重庆', '买房'], 'relevance': 2},
            {'title': '重庆各区房价对比', 'matched_keywords': ['重庆', '房价'], 'relevance': 2},
            {'title': '重庆地铁房分析', 'matched_keywords': ['重庆', '地铁', '配套'], 'relevance': 3},
            {'title': '重庆学区房盘点', 'matched_keywords': ['重庆', '学区'], 'relevance': 2},
        ]
        
        for item in evergreen_base:
            item['hot_level'] = 'low'
            item['is_evergreen'] = True
        
        topics.extend(evergreen_base)
        return topics
    
    def _save_candidates(self, candidates: List[Dict]):
        """保存候选选题"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = self.candidates_dir / f'candidates_{timestamp}.json'
        
        data = {
            'generated_at': datetime.now().isoformat(),
            'count': len(candidates),
            'candidates': candidates
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"候选选题已保存: {filepath}")
    
    def format_for_user(self, candidates: List[Dict]) -> str:
        """格式化选题列表供用户选择"""
        lines = [f"今日选题推荐（{datetime.now().strftime('%m/%d %H:%M')}）\n"]
        
        for i, topic in enumerate(candidates, 1):
            hot_icon = {'high': '[热]', 'medium': '[温]', 'low': '[常]'}.get(topic.get('hot_level', 'low'), '[常]')
            type_label = {
                'policy': '政策', 'market': '数据', 'hotspot': '热点', 
                'guide': '指南', 'opinion': '观点'
            }.get(topic.get('type', ''), '综合')
            
            lines.append(f"{i}. {hot_icon}【{type_label}】{topic['title']}")
            lines.append(f"   评分:{topic.get('score', 0)} | 来源:{topic.get('source_hotspot', '常青')[:15]}")
            if topic.get('keywords'):
                lines.append(f"   关键词: {', '.join(topic['keywords'][:3])}")
            lines.append('')
        
        lines.append("回复编号选择，或输入自定义选题")
        return '\n'.join(lines)


if __name__ == '__main__':
    engine = TopicEngineV2()
    candidates = engine.generate_candidates(count=8)
    print(engine.format_for_user(candidates))
