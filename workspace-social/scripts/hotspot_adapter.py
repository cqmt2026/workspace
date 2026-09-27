# -*- coding: utf-8 -*-
"""
热点数据适配器
将 V3.4 采集结果转换为 topic_engine / auto_writer / quality_checker 的输入格式

作者：可悦
版本：V1.0
日期：2026-06-14
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

SOCIAL_DIR = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-social')
HOTSPOTS_DIR = SOCIAL_DIR / 'memory' / '热点采集'
HOTSPOTS_BAK_DIR = SOCIAL_DIR / 'bank' / '房产专业' / 'pipeline_data' / 'hotspots'
OUTPUT_DIR = SOCIAL_DIR / 'bank' / '房产专业' / 'pipeline_data'


def load_v34_report(today: Optional[str] = None) -> List[Dict]:
    """
    读取 V3.4 采集报告的 JSON 格式
    返回带角度/评分的热点列表
    """
    if today is None:
        today = datetime.now().strftime('%Y-%m-%d')
    
    # V3.4 报告是 markdown 文件，但 main() 返回了 result 字典
    # 优先从 hot_topic_find.py 生成的 JSON 读取
    json_path = Path.home() / '.openclaw' / 'workspace' / 'memory' / '数据' / 'hot_topics' / f'hot_topics_{today}.json'
    if json_path.exists():
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('topics', [])
    
    return []


def convert_to_old_format(hotspots: List[Dict]) -> List[Dict]:
    """
    将 V3.4 格式转换为旧版 topic_engine 能读的格式
    """
    old_format = []
    for h in hotspots:
        old_format.append({
            'title': h.get('title', ''),
            'keyword': h.get('keyword', ''),
            'source': h.get('source', '头条搜索'),
            'score': h.get('score', 60),
            'angle': h.get('angle', '其他'),
            'author': h.get('author', ''),
            'date': h.get('date', ''),
            'age_days': h.get('age_days', 0),
            'is_re': h.get('is_re', True),
        })
    return old_format


def save_for_topic_engine(hotspots: List[Dict]):
    """
    保存为 topic_engine_v2 可读的格式
    """
    HOTSPOTS_BAK_DIR.mkdir(parents=True, exist_ok=True)
    
    old = convert_to_old_format(hotspots)
    
    fp = HOTSPOTS_BAK_DIR / f'hotspots_{datetime.now().strftime("%Y%m%d_%H%M")}.json'
    with open(fp, 'w', encoding='utf-8') as f:
        json.dump(old, f, ensure_ascii=False, indent=2)
    
    # 同时保存最新版（覆盖）
    latest = HOTSPOTS_BAK_DIR / 'hotspots_latest.json'
    with open(latest, 'w', encoding='utf-8') as f:
        json.dump(old, f, ensure_ascii=False, indent=2)
    
    print(f"[OK] 热点数据已保存: {fp} ({len(old)}条)")
    return str(fp)


def load_for_topic_engine() -> List[Dict]:
    """
    topic_engine 读取最新热点数据
    """
    latest = HOTSPOTS_BAK_DIR / 'hotspots_latest.json'
    if latest.exists():
        with open(latest, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


if __name__ == '__main__':
    # 测试适配器
    hots = load_v34_report()
    print(f"读取到 {len(hots)} 条热点")
    if hots:
        save_for_topic_engine(hots)
        print(f"示例: {hots[0]}")
    else:
        print("未找到热点数据，尝试直接读取采集报告")
        # 从 V3.4 的 markdown 报告提取标题
        today = datetime.now().strftime('%Y-%m-%d')
        md = HOTSPOTS_DIR / f'hotspot_{today}.md'
        if md.exists():
            content = md.read_text(encoding='utf-8')
            import re
            titles = re.findall(r'^\d+\.\s*\[.*?\]\[.*?\]\s*(.+)', content, re.MULTILINE)
            if titles:
                hots = [{'title': t.strip(), 'source': '头条搜索', 'score': 60, 'angle': '其他', 'is_re': True} for t in titles]
                save_for_topic_engine(hots)
                print(f"从markdown提取了 {len(hots)} 条")
