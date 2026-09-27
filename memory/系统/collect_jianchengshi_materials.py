# -*- coding: utf-8 -*-
"""
收集《鉴城师》题材相关知识素材
从 349 篇知识卡片中智能筛选与验房师、都市专业文相关的知识
"""

import json
from pathlib import Path
from datetime import datetime

print("=" * 80)
print("《鉴城师》题材相关知识素材收集")
print("=" * 80)
print(f"收集时间：{datetime.now().isoformat()}")

# 加载知识库
knowledge_base_file = Path('knowledge_base.json')
with open(knowledge_base_file, 'r', encoding='utf-8') as f:
    knowledge_base = json.load(f)

print(f"\n加载知识卡片：{knowledge_base['total_cards']}篇")

# 关键词匹配
keywords_jianchengshi = [
    # 验房相关
    '验房', '房屋', '建筑', '装修', '房产',
    # 都市相关
    '都市', '职场', '职业', '专业',
    # 爽点相关
    '开篇', '爽点', '打脸', '逆袭', '专业打脸',
    # 节奏相关
    '节奏', '高潮', '结局', '结局设计',
    # 职业文相关
    '职业文', '行业', '专业文', '行业文',
    # 开篇相关
    '开篇', '开头', '第一章', '新地图',
    # 爽点相关
    '爽点', '爆点', '燃点', '打脸',
    # 节奏相关
    '节奏', '节奏感', '高潮', '大高潮',
    # 结局相关
    '结局', '结局设计', '收官', '完美收官'
]

# 筛选相关知识卡片
relevant_cards = []

for card in knowledge_base['cards']:
    title = card.get('title', '').lower()
    tags = card.get('tags', [])
    category = card.get('category', '')
    
    # 匹配关键词
    score = 0
    matched_keywords = []
    
    for keyword in keywords_jianchengshi:
        if keyword in title.lower():
            score += 2
            matched_keywords.append(keyword)
        for tag in tags:
            if keyword in tag.lower():
                score += 1
                matched_keywords.append(tag)
    
    # 特定分类加分
    if category in ['writing_skills', 'writer_experience']:
        score += 1
    
    if score > 0:
        relevant_cards.append({
            'file': card['file'],
            'title': card['title'],
            'category': card['category'],
            'tags': card['tags'],
            'score': score,
            'matched_keywords': list(set(matched_keywords))
        })

# 按分数排序
relevant_cards.sort(key=lambda x: x['score'], reverse=True)

print(f"\n筛选出相关知识卡片：{len(relevant_cards)}篇")

# 分类整理
categories = {
    'writing_skills': [],
    'writer_experience': [],
    'platform_rules': [],
    'market_research': [],
    'other': []
}

for card in relevant_cards:
    categories[card['category']].append(card)

# 保存素材库
material_library = {
    'version': '1.0',
    'created_at': datetime.now().isoformat(),
    'novel': '鉴城师',
    'total_cards': len(relevant_cards),
    'categories': {
        cat: len(cards) for cat, cards in categories.items()
    },
    'cards': relevant_cards
}

# 保存
output_file = Path('jianchengshi_material_library.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(material_library, f, ensure_ascii=False, indent=2)

print(f"\n保存素材库：{output_file}")
print(f"文件大小：{output_file.stat().st_size / 1024:.1f}KB")

# 打印详细分类
print("\n" + "=" * 80)
print("分类统计")
print("=" * 80)

for category, cards in categories.items():
    if cards:
        print(f"\n{category} ({len(cards)}篇):")
        # 按分数排序，显示前 10 篇
        top_cards = sorted(cards, key=lambda x: x['score'], reverse=True)[:10]
        for i, card in enumerate(top_cards, 1):
            print(f"  {i}. {card['title']} (分数：{card['score']}, 匹配：{', '.join(card['matched_keywords'])})")

# 打印推荐清单
print("\n" + "=" * 80)
print("重点推荐清单")
print("=" * 80)

# 按阶段推荐
stages = {
    '开篇阶段 (51-60 章)': ['开篇', '开头', '新地图'],
    '发展阶段 (61-80 章)': ['发展', '节奏', '高潮'],
    '高潮阶段 (81-90 章)': ['高潮', '大高潮', '爽点'],
    '结局阶段 (91-100 章)': ['结局', '收官', '完美']
}

for stage, keywords in stages.items():
    print(f"\n{stage}:")
    
    stage_cards = [c for c in relevant_cards if any(kw in c['title'] for kw in keywords)]
    stage_cards = sorted(stage_cards, key=lambda x: x['score'], reverse=True)[:5]
    
    if stage_cards:
        for i, card in enumerate(stage_cards, 1):
            print(f"  {i}. {card['title']}")
    else:
        print("  无匹配卡片")

print("\n" + "=" * 80)
print("素材收集完成")
print("=" * 80)
