#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地图热点选题质量检查
检查选题是否包含地理/城市/经济相关关键词
"""
import json
from pathlib import Path
from datetime import datetime

TOPICS_DIR = Path(r"C:\Users\Administrator\.openclaw\workspace\workspace-maphot\data\topics")
GEO_KEYWORDS = ["城市", "地理", "经济", "数据", "统计", "区域", "地图", "区县", "人口", "GDP"]

def check_topics():
    """检查最新选题质量"""
    latest = None
    for f in TOPICS_DIR.glob("topics_*.json"):
        if latest is None or f.stat().st_mtime > latest.stat().st_mtime:
            latest = f
    
    if not latest:
        print("❌ 未找到选题文件")
        return
    
    with open(latest, encoding="utf-8") as fp:
        data = json.load(fp)
    
    topics = data.get("topics", [])
    geo_count = 0
    for t in topics[:10]:
        title = t.get("title", "")
        if any(kw in title for kw in GEO_KEYWORDS):
            geo_count += 1
    
    ratio = geo_count / min(len(topics), 10)
    print(f"选题质量: {geo_count}/10 包含地理关键词 ({ratio:.0%})")
    
    if ratio < 0.3:
        print("⚠️ 地理相关选题比例过低，建议调整采集源")
        return False
    return True

if __name__ == "__main__":
    check_topics()
