# -*- coding: utf-8 -*-
"""
第一阶段：知识卡片结构化
将 349 篇知识卡片提取关键信息，存储到结构化数据库
"""

import json
import re
from pathlib import Path
from datetime import datetime

print("=" * 60)
print("知识卡片结构化 - 第一阶段实施")
print("=" * 60)

# 配置
knowledge_base_path = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-novel\创作系统\L2-工具\03-知识库\知识卡')
output_file = Path(r'C:\Users\Administrator\.openclaw\workspace\memory\knowledge_base.json')

# 分类映射
category_mapping = {
    '01-作家课堂': 'writer_experience',
    '02-平台规则': 'platform_rules',
    '03-写作技巧': 'writing_skills',
    '04-市场调研': 'market_research',
    '05-其他': 'other'
}

# 流程节点映射
stage_mapping = {
    'writer_experience': ['topic_planning', 'outline_design', 'chapter_creation'],
    'platform_rules': ['quality_review', 'publish_operation'],
    'writing_skills': ['topic_planning', 'outline_design', 'chapter_creation'],
    'market_research': ['topic_planning'],
    'other': ['topic_planning', 'outline_design', 'chapter_creation', 'quality_review', 'publish_operation']
}

def extract_title(content):
    """提取标题"""
    match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    return match.group(1).strip() if match else '无标题'

def extract_tags(content):
    """提取标签"""
    tags = []
    # 从标题提取关键词
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if title_match:
        title = title_match.group(1)
        # 简单关键词提取
        keywords = ['开篇', '爽点', '对话', '节奏', '大纲', '爽点', '打脸', '逆袭']
        for kw in keywords:
            if kw in title:
                tags.append(kw)
    return tags if tags else ['通用']

def extract_key_points(content):
    """提取关键要点"""
    points = []
    # 提取二级标题下的内容
    sections = re.split(r'^##\s+', content, flags=re.MULTILINE)
    for section in sections[1:]:  # 跳过标题
        lines = section.split('\n')
        if lines:
            section_title = lines[0].strip()
            points.append(section_title)
    return points[:5]  # 最多 5 个要点

def extract_applicable_stages(category):
    """提取适用阶段"""
    return stage_mapping.get(category, ['topic_planning'])

def structure_knowledge_card(file_path, category):
    """将知识卡片结构化"""
    try:
        content = file_path.read_text(encoding='utf-8')
        
        structure = {
            'file': str(file_path),
            'title': extract_title(content),
            'category': category_mapping.get(category, 'other'),
            'tags': extract_tags(content),
            'key_points': extract_key_points(content),
            'applicable_stages': extract_applicable_stages(category),
            'content_preview': content[:200] + '...' if len(content) > 200 else content
        }
        
        return structure
    except Exception as e:
        print(f"  [WARN] 处理失败：{file_path.name} - {e}")
        return None

# 开始处理
print("\n开始处理知识卡片...")
print("-" * 40)

structured_cards = []
total_count = 0

for category in category_mapping.keys():
    category_path = knowledge_base_path / category
    if not category_path.exists():
        print(f"[SKIP] 分类不存在：{category}")
        continue
    
    md_files = list(category_path.glob('*.md'))
    print(f"\n处理分类：{category} ({len(md_files)}篇)")
    
    for md_file in md_files:
        structure = structure_knowledge_card(md_file, category)
        if structure:
            structured_cards.append(structure)
            total_count += 1
            
            if total_count % 50 == 0:
                print(f"  已处理：{total_count}篇")

# 保存到 JSON
print(f"\n保存结构化数据...")
print("-" * 40)

knowledge_base = {
    'version': '1.0',
    'created_at': datetime.now().isoformat(),
    'total_cards': total_count,
    'categories': {
        'writer_experience': len([c for c in structured_cards if c['category'] == 'writer_experience']),
        'platform_rules': len([c for c in structured_cards if c['category'] == 'platform_rules']),
        'writing_skills': len([c for c in structured_cards if c['category'] == 'writing_skills']),
        'market_research': len([c for c in structured_cards if c['category'] == 'market_research']),
        'other': len([c for c in structured_cards if c['category'] == 'other'])
    },
    'cards': structured_cards
}

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(knowledge_base, f, ensure_ascii=False, indent=2)

print(f"[OK] 保存到：{output_file}")
print(f"[OK] 总计：{total_count}篇知识卡片")
print(f"[OK] 分类统计:")
for cat, count in knowledge_base['categories'].items():
    print(f"  - {cat}: {count}篇")

# 验证
print(f"\n验证结构化数据...")
print("-" * 40)

with open(output_file, 'r', encoding='utf-8') as f:
    loaded_data = json.load(f)

if loaded_data['total_cards'] == total_count:
    print("[OK] 数据验证通过")
    print(f"[OK] 文件大小：{output_file.stat().st_size / 1024:.1f}KB")
else:
    print("[FAIL] 数据验证失败")

print("\n" + "=" * 60)
print("第一阶段完成 - 知识卡片结构化完成")
print("=" * 60)
