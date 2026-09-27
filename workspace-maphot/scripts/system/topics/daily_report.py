# -*- coding: utf-8 -*-
"""每日选题报告生成"""
import json, os, sys
from datetime import datetime

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
TOPICS_DIR = os.path.join(BASE_DIR, 'scripts', 'system', 'topics')

def load_today():
    today_str = datetime.now().strftime('%Y%m%d')
    path = os.path.join(TOPICS_DIR, f'topics_{today_str}.json')
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_recent(days=4):
    """加载近N天的选题，用于去重检查"""
    recent = []
    for i in range(1, days+1):
        d = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - __import__('datetime').timedelta(days=i)).strftime('%Y%m%d')
        path = os.path.join(TOPICS_DIR, f'topics_{d}.json')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                recent.extend(json.load(f))
    return recent

def analyze_topic(t):
    """分析单个选题的地图适配性"""
    title = t['title']
    score = t.get('score', 0)
    hot = t.get('hot', 0)
    
    # 地理关键词
    geo_kw = ['台风', '暴雨', '省份', '浙江', '东三省', '重庆', '深圳', '成都', '杭州', 
              'GDP', '经济', '人口', '面积', '排名', '天气', '气候', '高温', '省', '市']
    has_geo = any(kw in title for kw in geo_kw)
    
    # 故事关键词
    story_kw = ['女子', '宝宝', '宝妈', '考生', '游客', '司机', '员工', '公司', '阿姨', '师傅']
    has_story = any(kw in title for kw in story_kw)
    
    # 推荐类型
    rec_type = '待评估'
    map_type = ''
    reason = ''
    
    if '台风' in title:
        rec_type = '一张图'
        map_type = '区域高亮图 + 台风路径'
        reason = '台风影响区域可视化，地理属性强'
    elif '暴雨' in title or '天气' in title or '高温' in title:
        rec_type = '一张图'
        map_type = '全国俯视图 + 区域高亮'
        reason = '天气预警涉及区域分布'
    elif '泰国' in title or '游客' in title or '出境' in title:
        rec_type = '追热点'
        map_type = '中外对比地图'
        reason = '出境游话题，可对比国内外情况'
    elif '考生' in title or '警校' in title or '985' in title:
        rec_type = '追热点'
        map_type = '区域高亮图（城市）'
        reason = '教育话题，可讲城市选择'
    elif '科技' in title or '打破' in title or '垄断' in title:
        rec_type = '深一度'
        map_type = '全国布局图'
        reason = '科技成就，适合展示全国布局'
    elif '空调' in title:
        rec_type = '一张图'
        map_type = '数据阈值图'
        reason = '生活科普，可用数据对比'
    elif has_geo:
        rec_type = '一张图'
        map_type = '区域高亮图'
        reason = '地理相关，适合地图展示'
    elif has_story and hot > 7500000:
        rec_type = '追热点'
        map_type = '待定'
        reason = '故事性强，热度高，可考虑地图配合'
    
    return {
        'title': title,
        'score': score,
        'hot': hot,
        'has_geo': has_geo,
        'has_story': has_story,
        'rec_type': rec_type,
        'map_type': map_type,
        'reason': reason,
        'has_potential': rec_type != '待评估' or has_geo or has_story
    }

def main():
    today = load_today()
    recent = load_recent(4)
    recent_titles = [t['title'] for t in recent]
    
    # 去重
    dupes = [t for t in today if t['title'] in recent_titles]
    unique = [t for t in today if t['title'] not in recent_titles]
    
    print('=' * 60)
    print('  📍 每日选题采集报告')
    print(f'  日期: {datetime.now().strftime("%Y-%m-%d")}')
    print('=' * 60)
    print()
    print(f'【采集概况】')
    print(f'  今日选题总数: {len(today)}')
    print(f'  去重后新增: {len(unique)}')
    print(f'  与近4天重复: {len(dupes)}')
    print()
    
    if dupes:
        print(f'【重复选题（近4天已采集）】')
        for d in dupes:
            print(f'  ⚠️ {d["title"]}')
        print()
    
    print(f'【去重后 TOP 选题推荐】')
    analyzed = []
    for t in unique:
        info = analyze_topic(t)
        analyzed.append(info)
    
    # 按推荐优先级排序：有地图适配性的优先
    def priority(item):
        p = 0
        if item['rec_type'] == '一张图':
            p = 3
        elif item['rec_type'] == '追热点':
            p = 2
        elif item['rec_type'] == '深一度':
            p = 1
        else:
            p = 0
        return (p, item['hot'])
    
    analyzed.sort(key=priority, reverse=True)
    
    for i, info in enumerate(analyzed[:10], 1):
        badge = '🌟' if info['rec_type'] in ['一张图', '追热点'] else '  '
        print(f'  {badge} #{i} | {info["score"]}分 | {info["title"]}')
        print(f'      热度{info["hot"]:,.0f} | 推荐:{info["rec_type"]} | {info["reason"]}')
        if info['map_type']:
            print(f'      地图形式: {info["map_type"]}')
        print()
    
    # 写入报告文件
    report = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'total': len(today),
        'unique': len(unique),
        'duplicates': len(dupes),
        'topics': analyzed,
        'top_picks': [t['title'] for t in analyzed[:5]]
    }
    
    report_path = os.path.join(TOPICS_DIR, f'report_{datetime.now().strftime("%Y%m%d")}.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f'【报告已保存】{report_path}')
    print()
    
    # 输出供主系统读取
    print('=== TOP_PICKS ===')
    for t in analyzed[:5]:
        print(f'{t["title"]}|{t["rec_type"]}|{t["reason"]}')
    print('=== END ===')

if __name__ == '__main__':
    main()
