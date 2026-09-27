# -*- coding: utf-8 -*-
"""
选题采集模块 v2 — 增加官方数据源

数据源优先级：
1. 国家统计局（权威数据）
2. 各省市统计局（区域数据）
3. 发改委/工信部（政策动向）
4. 百度热搜（社会热点）
5. 微博热搜（舆论热点）
"""

import os
import sys
import json
import re
from datetime import datetime
from typing import List, Dict, Optional

# 添加路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    requests = None
    BeautifulSoup = None


class TopicLoader:
    """选题数据加载器"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.topics_dir = os.path.join(self.base_dir, 'system', 'topics')
    
    def load_today_topics(self):
        """
        加载今天的选题
        
        Returns:
            list: 今日选题列表，每个元素包含 {title, score, recommend, source, ...}
        """
        today = self._get_today_str()
        topics_file = os.path.join(self.topics_dir, f'topics_{today}.json')
        
        if not os.path.exists(topics_file):
            logger.warning(f"今日选题文件不存在: {topics_file}")
            return []
        
        with open(topics_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        topics = data.get('topics', [])
        logger.info(f"加载今日{len(topics)}个选题")
        return topics
    
    def get_top_topic(self, min_score=7):
        """
        获取最高分的选题（优先推荐有"为什么"角度的选题）
        
        Args:
            min_score: 最低分数阈值
            
        Returns:
            dict: 最高分选题，或None
        """
        topics = self.load_today_topics()
        if not topics:
            return None
        
        # 按score降序排序，优先选有"为什么"角度的
        def sort_key(t):
            s = t.get('score', 0)
            # 有"为什么"角度额外+2分
            why_bonus = 2 if '为什么' in t.get('title','') or '原因' in t.get('title','') or '揭秘' in t.get('title','') else 0
            return s + why_bonus
        
        sorted_topics = sorted(topics, key=sort_key, reverse=True)
        
        # 找到第一个>=min_score的
        for topic in sorted_topics:
            if topic.get('score', 0) >= min_score:
                return topic
        
        # 没有>=min_score的，返回最高分的
        return sorted_topics[0] if sorted_topics else None
    
    def get_topics_by_recommend(self, category="一张图"):
        """
        按栏目类型筛选选题
        
        Args:
            category: 栏目类型（一张图/追热点/深一度）
            
        Returns:
            list: 匹配的选题列表
        """
        topics = self.load_today_topics()
        return [t for t in topics if t.get('recommend') == category]
    
    def _get_today_str(self):
        from datetime import date
        return date.today().strftime('%Y%m%d')


def main():
    """测试：打印今日选题"""
    loader = TopicLoader()
    topics = loader.load_today_topics()
    
    print("=== 今日选题 ===")
    for t in topics[:10]:
        print(f"  #{t['title']} | score:{t['score']} | rec:{t['recommend']} | src:{t['source']}")
    
    top = loader.get_top_topic()
    if top:
        print(f"\n🏆 最高分选题: {top['title']} (score={top['score']}, recommend={top['recommend']})")


if __name__ == '__main__':
    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()
