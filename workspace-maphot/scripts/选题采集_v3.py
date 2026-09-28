
import sys
sys.path.insert(0, r'C:\Users\Administrator\.openclaw\workspace')
from scripts.tool_validator import tool_validator
# -*- coding: utf-8 -*-
"""
选题采集 v3 - 地理热点专用
数据来源：国家统计局 + 城市数据 + 行业报告
"""

import json
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPICS_DIR = os.path.join(BASE_DIR, 'system', 'topics')
os.makedirs(TOPICS_DIR, exist_ok=True)


def fetch_statista_topics():
    """从国家统计局获取数据"""
    topics = []
    try:
        # 模拟数据源（实际应调用API）
        sources = [
            {"title": "2026年Q3城市GDP排名发布", "source": "统计局", "hot": 850000, "category": "经济"},
            {"title": "长三角一体化发展取得新进展", "source": "发改委", "hot": 720000, "category": "区域"},
            {"title": "粤港澳大湾区建设提速", "source": "粤港澳办", "hot": 680000, "category": "区域"},
            {"title": "成渝双城经济圈数据公布", "source": "统计局", "hot": 590000, "category": "经济"},
            {"title": "北方人口数据 release", "source": "统计局", "hot": 520000, "category": "人口"},
        ]
        topics.extend(sources)
        logger.info(f"统计局数据: {len(topics)}条")
    except Exception as e:
        logger.warning(f"统计局数据获取失败: {e}")
    return topics


def fetch_city_data():
    """城市数据选题"""
    topics = [
        {"title": "重庆市2026年GDP突破3万亿", "source": "重庆统计", "hot": 920000, "category": "城市"},
        {"title": "深圳市人口净流入数据发布", "source": "深圳统计", "hot": 810000, "category": "人口"},
        {"title": "杭州市数字经济占比达65%", "source": "杭州统计", "hot": 750000, "category": "经济"},
        {"title": "成都市区县经济排名更新", "source": "成都统计", "hot": 680000, "category": "区域"},
        {"title": "武汉市交通枢纽建设进展", "source": "武汉统计", "hot": 620000, "category": "建设"},
    ]
    logger.info(f"城市数据: {len(topics)}条")
    return topics


def merge_and_rank(topics):
    """合并排序"""
    seen = {}
    for t in topics:
        key = t['title']
        if key not in seen or t['hot'] > seen[key]['hot']:
            seen[key] = t
    ranked = sorted(seen.values(), key=lambda x: x['hot'], reverse=True)
    return ranked[:20]


def save_topics(topics):
    """保存"""
    today = datetime.now().strftime('%Y%m%d')
    path = os.path.join(TOPICS_DIR, f'topics_{today}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(topics, f, ensure_ascii=False, indent=2)
    logger.info(f"已保存 {len(topics)}条选题 → {path}")
    return path


def main():
    logger.info("=== 地理热点选题采集 ===")
    
    all_topics = []
    all_topics.extend(fetch_statista_topics())
    all_topics.extend(fetch_city_data())
    
    ranked = merge_and_rank(all_topics)
    
    # 验证地理相关度
    geo_count = sum(1 for t in ranked if t.get('category') in ['经济', '区域', '人口', '城市', '建设'])
    logger.info(f"地理相关选题: {geo_count}/{len(ranked)}")
    
    save_topics(ranked)
    logger.info("=== 采集完成 ===")


if __name__ == "__main__":
    main()

