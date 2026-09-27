# -*- coding: utf-8 -*-
"""
第三阶段：推荐引擎开发
开发知识推荐引擎，实现智能推荐
"""

import json
from pathlib import Path
from datetime import datetime

print("=" * 60)
print("推荐引擎开发 - 第三阶段实施")
print("=" * 60)

# 加载知识卡片结构化数据
knowledge_base_file = Path(r'C:\Users\Administrator\.openclaw\workspace\memory\knowledge_base.json')
with open(knowledge_base_file, 'r', encoding='utf-8') as f:
    knowledge_base = json.load(f)

print(f"\n加载知识卡片：{knowledge_base['total_cards']}篇")

# 开发推荐引擎类
recommendation_engine_code = '''# -*- coding: utf-8 -*-
"""
知识推荐引擎
根据场景、阶段、标签智能推荐知识卡片
"""

import json
from pathlib import Path
from typing import Dict, List

class KnowledgeRecommender:
    """知识推荐引擎"""
    
    def __init__(self):
        # 加载知识库
        knowledge_base_file = Path(__file__).parent / 'knowledge_base.json'
        with open(knowledge_base_file, 'r', encoding='utf-8') as f:
            self.knowledge_base = json.load(f)
        
        # 加载流程节点定义
        workflow_file = Path(__file__).parent / 'workflow_definition.json'
        with open(workflow_file, 'r', encoding='utf-8') as f:
            self.workflow = json.load(f)
        
        print(f"[OK] 知识推荐引擎初始化完成")
        print(f"  - 知识卡片：{self.knowledge_base['total_cards']}篇")
        print(f"  - 流程节点：{self.workflow['total_stages']}个")
    
    def recommend_for_stage(self, stage_name: str, limit: int = 10) -> List[Dict]:
        """根据阶段推荐知识卡片"""
        stages = self.workflow['stages']
        
        if stage_name not in stages:
            return []
        
        stage = stages[stage_name]
        recommended = stage.get('recommended_cards_list', [])
        
        return recommended[:limit]
    
    def recommend_by_category(self, category: str, limit: int = 10) -> List[Dict]:
        """根据分类推荐知识卡片"""
        cards = [c for c in self.knowledge_base['cards'] if c['category'] == category]
        return cards[:limit]
    
    def recommend_by_tags(self, tags: List[str], limit: int = 10) -> List[Dict]:
        """根据标签推荐知识卡片"""
        scored_cards = []
        
        for card in self.knowledge_base['cards']:
            score = 0
            for tag in tags:
                if tag in card.get('tags', []):
                    score += 1
                if tag in card.get('title', ''):
                    score += 2
            
            if score > 0:
                scored_cards.append({
                    'card': card,
                    'score': score
                })
        
        # 按分数排序
        scored_cards.sort(key=lambda x: x['score'], reverse=True)
        
        return [sc['card'] for sc in scored_cards[:limit]]
    
    def recommend_for_writing(self, scene_type: str, limit: int = 10) -> List[Dict]:
        """根据写作场景推荐"""
        # 场景类型映射到标签
        scene_to_tags = {
            'opening': ['开篇', '开头'],
            'climax': ['高潮', '爽点', '打脸'],
            'dialogue': ['对话', '台词'],
            'ending': ['结尾', '结局'],
            'outline': ['大纲', '结构']
        }
        
        tags = scene_to_tags.get(scene_type, [])
        return self.recommend_by_tags(tags, limit)
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return {
            'total_cards': self.knowledge_base['total_cards'],
            'categories': self.knowledge_base['categories'],
            'total_stages': self.workflow['total_stages']
        }


# 测试
if __name__ == '__main__':
    recommender = KnowledgeRecommender()
    
    print("\\n" + "=" * 60)
    print("推荐引擎测试")
    print("=" * 60)
    
    # 测试阶段推荐
    print("\\n测试阶段推荐:")
    for stage in ['topic_planning', 'outline_design', 'chapter_creation']:
        cards = recommender.recommend_for_stage(stage, limit=3)
        print(f"\\n{stage}:")
        for card in cards:
            print(f"  - {card['title']}")
    
    # 测试标签推荐
    print("\\n测试标签推荐:")
    cards = recommender.recommend_by_tags(['开篇', '爽点'], limit=5)
    for card in cards:
        print(f"  - {card['title']} (标签：{card['tags']})")
    
    # 测试场景推荐
    print("\\n测试场景推荐:")
    cards = recommender.recommend_for_writing('opening', limit=5)
    for card in cards:
        print(f"  - {card['title']}")
    
    # 统计信息
    print("\\n统计信息:")
    stats = recommender.get_statistics()
    print(f"  总卡片数：{stats['total_cards']}")
    print(f"  总阶段数：{stats['total_stages']}")
'''

# 保存推荐引擎
output_file = Path(r'C:\Users\Administrator\.openclaw\workspace\memory\knowledge_recommender.py')

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(recommendation_engine_code)

print(f"\n保存推荐引擎...")
print("-" * 40)
print(f"[OK] 保存到：{output_file}")
print(f"[OK] 文件大小：{output_file.stat().st_size / 1024:.1f}KB")

# 测试推荐引擎
print(f"\n测试推荐引擎...")
print("-" * 40)

import sys
sys.path.insert(0, str(Path(__file__).parent))

from knowledge_recommender import KnowledgeRecommender

recommender = KnowledgeRecommender()

print("\n[OK] 推荐引擎开发完成")

print("\n" + "=" * 60)
print("第三阶段完成 - 推荐引擎开发完成")
print("=" * 60)
