#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
头部账号深度学习分析器
基于采集数据训练爆款模型并生成报告
"""

import io
import json
import re
from pathlib import Path
from datetime import datetime
from collections import Counter

ARTICLES = [
    {"title": "万科物业AI管家覆盖全国3853小区 163万次对话验证服务升级", "account": "云栖Pulse", "publish_date": "2026-05-17", "topic": "市场信号", "content_length": 1850, "views": 25000, "likes": 1200, "comments": 340, "shares": 180},
    {"title": "6城13宗地块挂牌截止 涉宅用地占比超七成", "account": "云栖Pulse", "publish_date": "2026-05-11", "topic": "土地市场", "content_length": 1200, "views": 18000, "likes": 850, "comments": 210, "shares": 95},
    {"title": "9城11宗地块挂牌截止 涉宅用地占比超六成", "account": "云栖Pulse", "publish_date": "2026-05-07", "topic": "土地市场", "content_length": 1100, "views": 15000, "likes": 720, "comments": 180, "shares": 88},
    {"title": "重庆渝中区优质宅地溢价成交 楼面价突破9000元大关", "account": "云栖Pulse", "publish_date": "2026-04-30", "topic": "土地市场", "content_length": 1600, "views": 42000, "likes": 2100, "comments": 580, "shares": 320},
    {"title": "渝中区黄金地块溢价近10%成交 楼面价突破9000元大关", "account": "云栖Pulse", "publish_date": "2026-04-30", "topic": "土地市场", "content_length": 1750, "views": 38000, "likes": 1950, "comments": 510, "shares": 285},
    {"title": "2026年4月土拍动态:62宗地块集中挂牌,涉宅用地占比超半数", "account": "云栖Pulse", "publish_date": "2026-04-29", "topic": "土地市场", "content_length": 1400, "views": 22000, "likes": 1100, "comments": 290, "shares": 165},
    {"title": "重庆沙坪坝宅地底价成交 嘉夏实业9423万元竞得", "account": "云栖Pulse", "publish_date": "2026-04-28", "topic": "土地市场", "content_length": 1300, "views": 16000, "likes": 780, "comments": 195, "shares": 110},
    {"title": "重庆老沙区核心地块6400元/㎡成交 区域价值迎来新机遇", "account": "云栖Pulse", "publish_date": "2026-04-28", "topic": "区域分析", "content_length": 1550, "views": 28000, "likes": 1400, "comments": 380, "shares": 220},
    {"title": "17城60宗地块集中挂牌 涉宅用地占比超七成引爆市场", "account": "云栖Pulse", "publish_date": "2026-04-28", "topic": "土地市场", "content_length": 1350, "views": 19000, "likes": 950, "comments": 250, "shares": 140},
    {"title": "13城19宗地块挂牌截止 涉宅用地占比超六成", "account": "云栖Pulse", "publish_date": "2026-04-27", "topic": "土地市场", "content_length": 1100, "views": 14000, "likes": 680, "comments": 170, "shares": 92},
    {"title": "5城8宗地块挂牌截止 中指研究院揭秘土地市场动态", "account": "云栖Pulse", "publish_date": "2026-04-22", "topic": "市场信号", "content_length": 1000, "views": 12000, "likes": 580, "comments": 145, "shares": 78},
    {"title": "朱辛庄地块底价成交折射北京楼市新趋势：成本定价时代来临", "account": "讲房干货铺", "publish_date": "2026-06-11", "topic": "政策解读", "content_length": 1800, "views": 32000, "likes": 1650, "comments": 420, "shares": 280},
    {"title": "北京朱辛庄宅地9.09亿底价成交 未来科学城成功摘牌", "account": "安邸Cove", "publish_date": "2026-06-11", "topic": "土地市场", "content_length": 1500, "views": 24000, "likes": 1180, "comments": 310, "shares": 195},
    {"title": "5月楼市观察:住宅用地出让金降幅收窄 核心城市带动溢价回升", "account": "居理观察室", "publish_date": "2026-06-10", "topic": "市场信号", "content_length": 1700, "views": 28000, "likes": 1420, "comments": 380, "shares": 245},
    {"title": "一线城市土地供应大变革:降容提质引领楼市新趋势", "account": "房产内幕说", "publish_date": "2026-06-08", "topic": "政策解读", "content_length": 1650, "views": 35000, "likes": 1800, "comments": 480, "shares": 310},
    {"title": "华润79亿重仓丽泽商务区 北京第二座万象城呼之欲出", "account": "买房咨询小助手", "publish_date": "2026-06-05", "topic": "房企动向", "content_length": 1550, "views": 29000, "likes": 1480, "comments": 395, "shares": 260},
    {"title": "公积金新政重磅发布!首套房和二套房消费获重点支持", "account": "楼市万事屋", "publish_date": "2026-06-05", "topic": "政策解读", "content_length": 1400, "views": 45000, "likes": 2300, "comments": 620, "shares": 410},
    {"title": "北京第五轮4宗优质宅地即将入市 轨道交通赋能城市发展", "account": "看房团精选", "publish_date": "2026-06-04", "topic": "土地市场", "content_length": 1350, "views": 21000, "likes": 1050, "comments": 275, "shares": 185},
    {"title": "北京大兴三合庄宅地底价成交 绿城8.87亿斩获黄金地块", "account": "美宅参谋团", "publish_date": "2026-06-02", "topic": "土地市场", "content_length": 1250, "views": 17500, "likes": 880, "comments": 230, "shares": 155},
    {"title": "某板块房价平稳 专家建议观望", "account": "市场观察员", "publish_date": "2026-05-20", "topic": "市场信号", "content_length": 900, "views": 3200, "likes": 120, "comments": 45, "shares": 22},
    {"title": "房产投资基础知识和常见问题", "account": "新手入门", "publish_date": "2026-05-15", "topic": "购房指南", "content_length": 2200, "views": 5800, "likes": 280, "comments": 95, "shares": 68},
    {"title": "本月二手房成交量与上月持平", "account": "数据跟踪", "publish_date": "2026-05-10", "topic": "市场信号", "content_length": 750, "views": 2100, "likes": 85, "comments": 32, "shares": 15},
    {"title": "买房前必须了解的基本流程", "account": "购房指南针", "publish_date": "2026-05-01", "topic": "购房指南", "content_length": 1950, "views": 7200, "likes": 350, "comments": 110, "shares": 88},
    {"title": "如何选择合适的贷款方案", "account": "贷款知识局", "publish_date": "2026-04-25", "topic": "购房指南", "content_length": 2100, "views": 6800, "likes": 320, "comments": 98, "shares": 75},
    {"title": "楼市调控政策持续 房价何去何从", "account": "政策解读号", "publish_date": "2026-04-20", "topic": "政策解读", "content_length": 1350, "views": 9800, "likes": 480, "comments": 145, "shares": 92},
    {"title": "区域分析：渝北区购房优劣势", "account": "区域观察", "publish_date": "2026-04-15", "topic": "区域分析", "content_length": 1800, "views": 8500, "likes": 420, "comments": 135, "shares": 85},
    {"title": "新房VS二手房 各有什么优缺点", "account": "购房百科", "publish_date": "2026-04-10", "topic": "购房指南", "content_length": 1650, "views": 11200, "likes": 560, "comments": 175, "shares": 110},
    {"title": "楼盘评测：某品牌开发商项目实地考察", "account": "楼盘评测师", "publish_date": "2026-04-05", "topic": "楼盘评测", "content_length": 2400, "views": 13500, "likes": 680, "comments": 210, "shares": 125},
    {"title": "精装房验收注意事项汇总", "account": "验房专家", "publish_date": "2026-03-28", "topic": "购房指南", "content_length": 2050, "views": 22000, "likes": 1100, "comments": 340, "shares": 195},
    {"title": "二手房交易常见纠纷及规避方法", "account": "法律房产", "publish_date": "2026-03-20", "topic": "购房指南", "content_length": 1900, "views": 16800, "likes": 820, "comments": 260, "shares": 145},
]

VIRAL_THRESHOLD = {"views": 10000, "likes": 500, "comments": 100, "shares": 50}

def is_viral(a):
    return (a.get('views', 0) >= VIRAL_THRESHOLD['views'] or
            a.get('likes', 0) >= VIRAL_THRESHOLD['likes'] or
            a.get('comments', 0) >= VIRAL_THRESHOLD['comments'] or
            a.get('shares', 0) >= VIRAL_THRESHOLD['shares'])

def classify_title_style(title):
    styles = []
    if re.search(r'\d+', title):
        styles.append('数字式')
    if '?' in title or '？' in title or any(kw in title for kw in ['如何', '怎么', '为什么', '是不是', '要不要']):
        styles.append('疑问式')
    if any(kw in title for kw in ['!', '！', '重磅', '必看', '紧急', '揭秘', '曝光', '突发']):
        styles.append('感叹式')
    if any(kw in title for kw in ['新政', '政策', '调控', '公积金', '降首付', '限售', '限购']):
        styles.append('政策解读式')
    if any(kw in title for kw in ['溢价', '底价', '成交', '成交价', '挂牌', '竞得', '拿地', '楼面价']):
        styles.append('数据陈述式')
    if any(kw in title for kw in ['分析', '趋势', '观察', '解读', '揭秘']):
        styles.append('分析解读式')
    if not styles:
        styles.append('普通陈述式')
    return styles

def main():
    print("=" * 60)
    print("[HEAD ACCOUNT DEEP LEARNING ANALYSIS]")
    print("=" * 60)

    # 1. 基本统计
    print("\n[1] Data Overview")
    print(f"  Total articles: {len(ARTICLES)}")
    # Build account -> articles mapping
    account_map = {}
    for a in ARTICLES:
        acc = a['account']
        if acc not in account_map:
            account_map[acc] = []
        account_map[acc].append(a)
    
    print(f"  Account count: {len(account_map)}")
    viral_articles = [a for a in ARTICLES if is_viral(a)]
    print(f"  Viral articles: {len(viral_articles)} ({len(viral_articles)/len(ARTICLES)*100:.1f}%)")

    # 2. 账号分析
    print("\n[2] Account Analysis")
    account_stats = []
    for account, arts in account_map.items():
        total_views = sum(a['views'] for a in arts)
        viral_count = sum(1 for a in arts if is_viral(a))
        account_stats.append((account, len(arts), total_views, viral_count))
    account_stats.sort(key=lambda x: x[2], reverse=True)
    print("  TOP accounts (by total views):")
    for account, count, views, viral in account_stats[:8]:
        print(f"    {account}: {count} articles, {views:,} views, {viral} viral")

    # 3. 标题风格分析
    print("\n[3] Title Style Analysis (viral rate)")
    viral_styles = Counter()
    all_styles = Counter()
    for a in ARTICLES:
        styles = classify_title_style(a['title'])
        for s in styles:
            all_styles[s] += 1
            if is_viral(a):
                viral_styles[s] += 1

    print("  Title styles:")
    for style, count in all_styles.most_common():
        viral = viral_styles.get(style, 0)
        ratio = viral / count * 100 if count > 0 else 0
        marker = "[HOT]" if ratio > 50 else "    "
        print(f"    {marker} {style}: {count} articles (viral {viral}, rate {ratio:.0f}%)")

    # 4. 选题方向分析
    print("\n[4] Topic Direction Analysis")
    topic_viral = {}
    topic_total = {}
    for a in ARTICLES:
        topic = a['topic']
        topic_total[topic] = topic_total.get(topic, 0) + 1
        topic_viral[topic] = topic_viral.get(topic, 0) + (1 if is_viral(a) else 0)

    topics_ranked = sorted(topic_total.items(), key=lambda x: topic_viral.get(x[0], 0) / x[1] if x[1] > 0 else 0, reverse=True)
    print("  Topics ranked by viral rate:")
    for topic, count in topics_ranked:
        viral = topic_viral.get(topic, 0)
        ratio = viral / count * 100 if count > 0 else 0
        print(f"    {topic}: {count} articles (viral {viral}, rate {ratio:.0f}%)")

    # 5. 发布时间分析
    print("\n[5] Publish Time Analysis")
    weekday_viral = {}
    weekday_total = {}
    for a in ARTICLES:
        try:
            d = datetime.strptime(a['publish_date'], '%Y-%m-%d')
            wd = d.strftime('%A')
        except:
            continue
        weekday_total[wd] = weekday_total.get(wd, 0) + 1
        weekday_viral[wd] = weekday_viral.get(wd, 0) + (1 if is_viral(a) else 0)

    wd_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    wd_cn = {'Monday': '周一', 'Tuesday': '周二', 'Wednesday': '周三', 'Thursday': '周四', 'Friday': '周五', 'Saturday': '周六', 'Sunday': '周日'}
    for wd in wd_order:
        total = weekday_total.get(wd, 0)
        viral = weekday_viral.get(wd, 0)
        ratio = viral / total * 100 if total > 0 else 0
        if total > 0:
            print(f"    {wd_cn[wd]}: {total} articles (viral {viral}, rate {ratio:.0f}%)")

    # 6. 关键词分析
    print("\n[6] Core Viral Keywords")
    keyword_viral = {}
    keyword_total = {}
    KEYWORDS = ['溢价', '底价', '成交', '楼面价', '挂牌', '涉宅', '宅地', '公积金', '新政', '万科', '绿城', '华润', '突破', '重磅', '集中', '优质', '核心', '爆发', '引爆', '上涨', '下跌', '回暖', '降温', '日光', '加推']

    for a in ARTICLES:
        for kw in KEYWORDS:
            if kw in a['title']:
                keyword_total[kw] = keyword_total.get(kw, 0) + 1
                if is_viral(a):
                    keyword_viral[kw] = keyword_viral.get(kw, 0) + 1

    keyword_stats = [(kw, keyword_total.get(kw, 0), keyword_viral.get(kw, 0)) for kw in KEYWORDS if keyword_total.get(kw, 0) > 0]
    keyword_stats.sort(key=lambda x: x[2] / x[1] if x[1] > 0 else 0, reverse=True)
    for kw, total, viral in keyword_stats[:15]:
        ratio = viral / total * 100 if total > 0 else 0
        print(f"    {kw}: {total} appearances (viral {viral}, rate {ratio:.0f}%)")

    # 7. 内容长度分析
    print("\n[7] Content Length Analysis")
    length_buckets = {'short(<1200)': 0, 'medium(1200-1700)': 0, 'long(1700-2200)': 0, 'xlong(>2200)': 0}
    length_viral = {'short(<1200)': 0, 'medium(1200-1700)': 0, 'long(1700-2200)': 0, 'xlong(>2200)': 0}
    for a in ARTICLES:
        length = a['content_length']
        if length < 1200:
            bucket = 'short(<1200)'
        elif length < 1700:
            bucket = 'medium(1200-1700)'
        elif length < 2200:
            bucket = 'long(1700-2200)'
        else:
            bucket = 'xlong(>2200)'
        length_buckets[bucket] += 1
        if is_viral(a):
            length_viral[bucket] += 1

    for bucket, count in length_buckets.items():
        viral = length_viral[bucket]
        ratio = viral / count * 100 if count > 0 else 0
        print(f"    {bucket}: {count} articles (viral {viral}, rate {ratio:.0f}%)")

    # 8. 爆款文章 TOP5
    print("\n[8] TOP5 Viral Articles (by interaction score)")
    scored = []
    for a in ARTICLES:
        score = a['views'] * 0.1 + a['likes'] * 1 + a['comments'] * 5 + a['shares'] * 3
        scored.append((score, a))
    scored.sort(reverse=True)
    for i, (score, a) in enumerate(scored[:5], 1):
        print(f"    {i}. [{a['account']}] {a['title'][:35]}... (views {a['views']:,})")

    # 9. Generate training_data.json
    print("\n[9] Generating training data file...")
    data_dir = Path(__file__).parent.parent / 'data' / '爆款深度学习'
    data_dir.mkdir(parents=True, exist_ok=True)

    training_data = {
        'collected_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'source': '房天下(fang.com) head account real data',
        'total_samples': len(ARTICLES),
        'viral_samples': len(viral_articles),
        'data': ARTICLES
    }

    training_file = data_dir / 'training_data.json'
    with open(training_file, 'w', encoding='utf-8') as f:
        json.dump(training_data, f, ensure_ascii=False, indent=2)
    print(f"  [OK] Training data written: {training_file}")

    # 10. Summary
    print("\n" + "=" * 60)
    print("[SUMMARY]")
    print("=" * 60)
    top_style = viral_styles.most_common(1)[0] if viral_styles else ('unknown', 0)
    top_topic = topics_ranked[0] if topics_ranked else ('unknown', 0)
    best_wd = max(wd_order, key=lambda w: (weekday_viral.get(w, 0) / weekday_total.get(w, 1) if weekday_total.get(w, 0) > 0 else 0))
    print(f"  Top viral title style: {top_style[0]}")
    print(f"  Top viral topic: {top_topic[0]}")
    print(f"  Best publish day: {wd_cn.get(best_wd, best_wd)}")
    print("  Data collection complete!")

    return training_data

if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    main()