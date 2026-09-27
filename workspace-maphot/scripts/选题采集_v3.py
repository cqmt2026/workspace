# -*- coding: utf-8 -*-
"""
选题采集 v3 - 独立可执行脚本
采集百度热搜 + 微博热搜，输出到 system/topics/
添加地理关键词过滤
"""

import json
import os
import re
import logging
from datetime import datetime

import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPICS_DIR = os.path.join(BASE_DIR, 'system', 'topics')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

os.makedirs(TOPICS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# 地理相关关键词
GEO_KEYWORDS = ["城市", "地理", "经济", "数据", "统计", "区域", "地图", "区县", "人口", "GDP", "产业", "投资", "建设", "交通", "教育", "医疗"]


def fetch_baidu():
    """抓取百度热搜"""
    topics = []
    try:
        r = requests.get('https://top.baidu.com/board?tab=realtime',
                         headers=HEADERS, timeout=15)
        r.encoding = 'utf-8'
        words = re.findall(r'"word":"([^"]+)"', r.text)
        scores = re.findall(r'"hotScore":(\d+)', r.text)
        for i, w in enumerate(words[:20]):
            score = int(scores[i]) if i < len(scores) else 0
            topics.append({
                'title': w,
                'source': 'baidu',
                'hot': score,
                'score': min(score // 100000, 120),
                'category': '综合',
            })
        logger.info(f"百度热搜: {len(topics)}条")
    except Exception as e:
        logger.warning(f"百度热搜抓取失败: {e}")
    return topics


def fetch_weibo():
    """抓取微博热搜"""
    topics = []
    try:
        r = requests.get('https://weibo.com/ajax/side/hotSearch',
                         headers={**HEADERS, 'Referer': 'https://weibo.com'},
                         timeout=10)
        data = r.json()
        for item in data.get('data', {}).get('realtime', []):
            word = item.get('word', '')
            hot = item.get('raw_hot', 0) or item.get('num', 0)
            if not word:
                continue
            topics.append({
                'title': word,
                'source': 'weibo',
                'hot': hot,
                'score': min(hot // 100000, 120),
                'category': '综合',
            })
        logger.info(f"微博热搜: {len(topics)}条")
    except Exception as e:
        logger.warning(f"微博热搜抓取失败: {e}")
    return topics


def filter_geo_topics(topics):
    """过滤地理相关选题"""
    filtered = []
    for t in topics:
        title = t.get('title', '')
        if any(kw in title for kw in GEO_KEYWORDS):
            t['category'] = '地理'
            filtered.append(t)
        else:
            t['category'] = '综合'
    return filtered


def merge_and_rank(topics):
    """合并并排序"""
    seen = {}
    for t in topics:
        key = t['title']
        if key not in seen or t['hot'] > seen[key]['hot']:
            seen[key] = t
    ranked = sorted(seen.values(), key=lambda x: x['hot'], reverse=True)
    return ranked[:20]


def save_topics(topics):
    """保存到 system/topics/"""
    today = datetime.now().strftime('%Y%m%d')
    path = os.path.join(TOPICS_DIR, f'topics_{today}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(topics, f, ensure_ascii=False, indent=2)
    logger.info(f"已保存 {len(topics)}条选题 → {path}")
    return path


def main():
    logger.info("=== 开始选题采集 ===")

    all_topics = []
    all_topics.extend(fetch_baidu())
    all_topics.extend(fetch_weibo())

    # 地理关键词过滤
    geo_filtered = filter_geo_topics(all_topics)
    geo_topics = [t for t in geo_filtered if t['category'] == '地理']

    if geo_topics:
        logger.info(f"地理相关选题: {len(geo_topics)}条")
        ranked = merge_and_rank(geo_topics)
    else:
        logger.warning("无地理相关选题，使用原始数据")
        ranked = merge_and_rank(all_topics)

    save_topics(ranked)
    logger.info("=== 采集完成 ===")


if __name__ == "__main__":
    main()
