# -*- coding: utf-8 -*-
"""
第二阶段：流程节点定义
为 5 个创作流程节点定义详细规范和知识映射
"""

import json
from pathlib import Path
from datetime import datetime

print("=" * 60)
print("流程节点定义 - 第二阶段实施")
print("=" * 60)

# 加载知识卡片结构化数据
knowledge_base_file = Path(r'C:\Users\Administrator\.openclaw\workspace\memory\knowledge_base.json')
with open(knowledge_base_file, 'r', encoding='utf-8') as f:
    knowledge_base = json.load(f)

print(f"\n加载知识卡片：{knowledge_base['total_cards']}篇")

# 定义 5 个流程节点
workflow_stages = {
    'topic_planning': {
        'name': '选题规划',
        'description': '根据市场热点和作家经验，确定小说题材和定位',
        'input': ['作者偏好', '市场数据'],
        'output': '选题规划报告',
        'knowledge_categories': ['market_research', 'writer_experience'],
        'recommended_cards': 10,
        'template': '选题规划模板'
    },
    'outline_design': {
        'name': '大纲设计',
        'description': '根据选题设计小说大纲、结构和节奏',
        'input': ['选题报告', '写作技巧'],
        'output': '小说大纲',
        'knowledge_categories': ['writing_skills', 'writer_experience'],
        'recommended_cards': 15,
        'template': '大纲设计模板'
    },
    'chapter_creation': {
        'name': '章节创作',
        'description': '根据大纲创作具体章节内容',
        'input': ['章节大纲', '写作技巧'],
        'output': '章节初稿',
        'knowledge_categories': ['writing_skills', 'writer_experience'],
        'recommended_cards': 20,
        'template': '章节创作模板'
    },
    'quality_review': {
        'name': '质量审核',
        'description': '根据平台规则和质量标准审核章节',
        'input': ['章节内容', '平台规则'],
        'output': '质量审核报告',
        'knowledge_categories': ['platform_rules', 'writing_skills'],
        'recommended_cards': 10,
        'template': '质量审核模板'
    },
    'publish_operation': {
        'name': '发布运营',
        'description': '根据平台规则和运营技巧发布和运营作品',
        'input': ['审核通过的章节', '运营策略'],
        'output': '发布运营方案',
        'knowledge_categories': ['platform_rules', 'writer_experience'],
        'recommended_cards': 10,
        'template': '发布运营模板'
    }
}

# 为每个节点推荐知识卡片
print("\n为流程节点推荐知识卡片...")
print("-" * 40)

for stage_key, stage in workflow_stages.items():
    print(f"\n处理节点：{stage['name']}")
    
    # 从知识库中筛选相关知识卡片
    recommended_cards = []
    for card in knowledge_base['cards']:
        if card['category'] in stage['knowledge_categories']:
            # 检查是否适用于该阶段
            if stage_key in card.get('applicable_stages', []):
                recommended_cards.append({
                    'file': card['file'],
                    'title': card['title'],
                    'category': card['category']
                })
    
    # 限制推荐数量
    if len(recommended_cards) > stage['recommended_cards']:
        recommended_cards = recommended_cards[:stage['recommended_cards']]
    
    stage['recommended_cards_list'] = recommended_cards
    print(f"  [OK] 推荐知识卡片：{len(recommended_cards)}篇")

# 保存流程节点定义
output_file = Path(r'C:\Users\Administrator\.openclaw\workspace\memory\workflow_definition.json')

workflow_definition = {
    'version': '1.0',
    'created_at': datetime.now().isoformat(),
    'total_stages': len(workflow_stages),
    'stages': workflow_stages
}

print(f"\n保存流程节点定义...")
print("-" * 40)

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(workflow_definition, f, ensure_ascii=False, indent=2)

print(f"[OK] 保存到：{output_file}")
print(f"[OK] 总计：{len(workflow_stages)}个流程节点")

# 验证
print(f"\n验证流程节点定义...")
print("-" * 40)

with open(output_file, 'r', encoding='utf-8') as f:
    loaded_definition = json.load(f)

if loaded_definition['total_stages'] == len(workflow_stages):
    print("[OK] 定义验证通过")
    print(f"[OK] 文件大小：{output_file.stat().st_size / 1024:.1f}KB")
else:
    print("[FAIL] 定义验证失败")

# 打印详细统计
print(f"\n流程节点详细统计:")
print("-" * 40)

for stage_key, stage in workflow_stages.items():
    print(f"\n{stage['name']} ({stage_key}):")
    print(f"  描述：{stage['description']}")
    print(f"  输入：{', '.join(stage['input'])}")
    print(f"  输出：{stage['output']}")
    print(f"  知识分类：{', '.join(stage['knowledge_categories'])}")
    print(f"  推荐卡片：{len(stage['recommended_cards_list'])}篇")

print("\n" + "=" * 60)
print("第二阶段完成 - 流程节点定义完成")
print("=" * 60)
