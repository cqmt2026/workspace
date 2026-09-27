# -*- coding: utf-8 -*-
"""
从选题库中挑选适合地图展示的优质选题

标准：
1. 包含具体数据（GDP/人口/排名等）
2. 有地理维度（省份/城市对比）
3. 有新闻价值或争议性
4. 数据可视化效果好
"""

import json
import re
from pathlib import Path

TOPICS_FILE = Path(__file__).parent.parent / 'data' / 'topics' / '202608' / 'topics_20260823.json'

# 优质选题特征
QUALITY_PATTERNS = [
    # 经济数据类（最适合排名视频）
    r'GDP', r'经济.*运行', r'增长.*\d+%?', r'下降.*\d+%?',
    r'消费.*总额', r'投资.*增长', r'进出口', r'出口.*激增',
    r'规模以上', r'工业产值', r'财政收入',
    
    # 人口数据类
    r'人口.*\d+万?', r'常住人口', r'老龄化', r'出生率',
    
    # 基础设施类
    r'地铁.*开通', r'高铁.*线路', r'机场.*吞吐量', r'港口.*排名',
    
    # 热点事件类
    r'演唱会', r'发布会', r'新闻发布', r'通报',
]

# 排除词
EXCLUDE_PATTERNS = [
    r'培训', r'考试', r'公示', r'通知', r'安排',
    r'购买', r'服务', r'招标', r'采购',
]


def is_quality_topic(title):
    """判断是否为优质选题"""
    # 排除无关内容
    for pat in EXCLUDE_PATTERNS:
        if re.search(pat, title):
            return False
    
    # 必须有数据或地名
    has_data = bool(re.search(r'\d+|%|增长|下降|排名|第一|第二', title))
    has_geo = bool(re.search(r'北京|上海|广东|浙江|江苏|四川|湖北|河南|山东|西安|成都|武汉|杭州|南京', title))
    has_num = bool(re.search(r'\d+', title))
    
    return has_data and has_num and len(title) > 10


def extract_key_data(title):
    """提取关键数据"""
    # 尝试提取百分比
    pct = re.search(r'(\d+\.?\d*)%?', title)
    if pct:
        return pct.group(1) + '%'
    
    # 尝试提取数字
    nums = re.findall(r'\d+', title)
    if nums:
        return nums[0]
    
    return None


def select_topics(topics, count=5):
    """挑选优质选题"""
    candidates = []
    
    for t in topics:
        title = t.get('title', '')
        if is_quality_topic(title):
            key_data = extract_key_data(title)
            candidates.append({
                'title': title,
                'source': t.get('source', ''),
                'geo_angle': t.get('geo_angle', ''),
                'score': t.get('score', 0),
                'key_data': key_data,
            })
    
    # 按分数排序，取前count个
    candidates.sort(key=lambda x: (-x['score'], len(x['title'])))
    return candidates[:count]


def generate_video_scripts(candidates):
    """为每个选题生成视频脚本框架"""
    scripts = []
    
    for i, c in enumerate(candidates, 1):
        title = c['title']
        
        # 生成文案钩子
        hook = f"你知道吗？{title.split()[0] if ' ' in title else title[:15]}..."
        
        # 生成标题
        video_title = f"【地图热点】{title[:30]}"
        
        # 生成地图角度
        map_type = c.get('geo_angle', '')
        
        # 生成数据要点
        data_points = []
        if '%' in str(c.get('key_data', '')):
            data_points.append(f"增长/下降 {c['key_data']}")
        data_points.append(f"来源: {c['source']}")
        
        scripts.append({
            'id': f'topic_{i:02d}',
            'title': title,
            'video_title': video_title,
            'hook': hook,
            'map_type': map_type,
            'data_points': data_points,
            'priority': 'high' if c['score'] >= 95 else 'medium',
        })
    
    return scripts


def main():
    print("\n" + "=" * 70)
    print("优质选题筛选与脚本生成")
    print("=" * 70)
    
    # 加载选题
    with open(TOPICS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    topics = data.get('topics', [])
    print(f"\n总选题数: {data.get('total', 0)}")
    print(f"有地理角度: {data.get('with_angle', 0)}")
    
    # 挑选优质选题
    candidates = select_topics(topics, count=5)
    
    print(f"\n筛选出优质选题: {len(candidates)}个\n")
    
    # 生成脚本
    scripts = generate_video_scripts(candidates)
    
    print("【TOP5 选题+脚本】\n")
    for i, s in enumerate(scripts, 1):
        print(f"{'='*60}")
        print(f"选题 {i}: {s['title'][:50]}...")
        print(f"视频标题: {s['video_title']}")
        print(f"开场钩子: {s['hook']}")
        print(f"地图角度: {s['map_type']}")
        print(f"数据要点: {' | '.join(s['data_points'])}")
        print(f"优先级: {s['priority']}")
        print()
    
    # 保存脚本
    output_file = Path(__file__).parent.parent / 'data' / 'topics' / '202608' / 'selected_topics.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'date': data.get('date', ''),
            'total_topics': len(topics),
            'selected': len(scripts),
            'scripts': scripts,
        }, f, ensure_ascii=False, indent=2)
    
    print(f"已保存: {output_file}")
    
    return scripts


if __name__ == '__main__':
    main()
