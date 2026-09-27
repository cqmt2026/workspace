# -*- coding: utf-8 -*-
"""
模板推荐系统
根据场景和用户历史，智能推荐模板
"""

from pathlib import Path
from typing import List, Dict
import json

# 模板库路径
TEMPLATE_FILE = Path(__file__).parent / 'templates.md'

# 模板元数据
TEMPLATE_METADATA = {
    'novel_chapter': {
        'scenes': ['novel'],
        'keywords': ['章节', '小说', '创作', '大纲'],
        'priority': 10,
        'description': '小说章节生成模板'
    },
    'social_media': {
        'scenes': ['social_media'],
        'keywords': ['自媒体', '文章', '热点', '发布'],
        'priority': 8,
        'description': '自媒体文章模板'
    },
    'market_report': {
        'scenes': ['analysis'],
        'keywords': ['分析', '调研', '报告', '市场'],
        'priority': 7,
        'description': '市场调研报告模板'
    },
    'session_summary': {
        'scenes': ['summary'],
        'keywords': ['总结', '摘要', '回顾', '记忆'],
        'priority': 6,
        'description': '会话摘要模板'
    }
}


class TemplateRecommender:
    """模板推荐系统"""
    
    def __init__(self):
        self.metadata = TEMPLATE_METADATA
        self.user_history = []  # 用户历史使用记录
    
    def recommend(self, scene: str, context: Dict = None, top_k: int = 3) -> List[Dict]:
        """
        推荐模板
        
        参数:
            scene: 场景类型
            context: 上下文信息
            top_k: 推荐数量
        
        返回:
            list: 推荐的模板列表
        """
        # 计算每个模板的得分
        scores = {}
        
        for template_key, meta in self.metadata.items():
            score = 0.0
            
            # 场景匹配（权重 50%）
            if scene in meta['scenes']:
                score += 0.5
            
            # 关键词匹配（权重 30%）
            if context and 'keywords' in context:
                keyword_matches = sum(1 for kw in meta['keywords'] if kw in context['keywords'])
                score += 0.3 * (keyword_matches / len(meta['keywords']))
            
            # 用户历史偏好（权重 20%）
            if self.user_history:
                usage_count = sum(1 for h in self.user_history if h.get('template') == template_key)
                score += 0.2 * (usage_count / len(self.user_history))
            
            # 优先级加成
            score += meta['priority'] / 100
            
            scores[template_key] = score
        
        # 排序并返回 top_k
        sorted_templates = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        recommendations = []
        for template_key, score in sorted_templates[:top_k]:
            recommendations.append({
                'template': template_key,
                'score': score,
                'description': self.metadata[template_key]['description'],
                'reason': self._generate_reason(template_key, scene, context)
            })
        
        return recommendations
    
    def _generate_reason(self, template_key: str, scene: str, context: Dict = None) -> str:
        """生成推荐理由"""
        reasons = []
        
        meta = self.metadata[template_key]
        
        # 场景匹配
        if scene in meta['scenes']:
            reasons.append(f'匹配场景：{scene}')
        
        # 关键词匹配
        if context and 'keywords' in context:
            matches = [kw for kw in meta['keywords'] if kw in context['keywords']]
            if matches:
                reasons.append(f'匹配关键词：{", ".join(matches)}')
        
        # 用户偏好
        if self.user_history:
            usage_count = sum(1 for h in self.user_history if h.get('template') == template_key)
            if usage_count > 2:
                reasons.append(f'您常用此模板（{usage_count}次）')
        
        return '; '.join(reasons) if reasons else '系统推荐'
    
    def record_usage(self, template_key: str, scene: str, feedback: str = 'positive'):
        """
        记录模板使用
        
        参数:
            template_key: 模板键
            scene: 场景类型
            feedback: 用户反馈 ('positive'/'negative')
        """
        self.user_history.append({
            'template': template_key,
            'scene': scene,
            'feedback': feedback,
            'timestamp': str(Path.home())
        })
        
        # 限制历史记录长度
        if len(self.user_history) > 100:
            self.user_history = self.user_history[-100:]


def main():
    """测试函数"""
    print('=' * 60)
    print('模板推荐系统测试')
    print('=' * 60)
    
    recommender = TemplateRecommender()
    
    # 测试场景 1：小说创作
    print('\n【测试 1】小说创作场景')
    context = {
        'keywords': ['章节', '小说', '创作', '大纲', '爽点']
    }
    recommendations = recommender.recommend('novel', context, top_k=3)
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['template']}")
        print(f"   描述：{rec['description']}")
        print(f"   得分：{rec['score']:.2f}")
        print(f"   理由：{rec['reason']}")
    
    # 测试场景 2：自媒体创作
    print('\n【测试 2】自媒体创作场景')
    context = {
        'keywords': ['自媒体', '文章', '热点', '爆款']
    }
    recommendations = recommender.recommend('social_media', context, top_k=3)
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['template']}")
        print(f"   描述：{rec['description']}")
        print(f"   得分：{rec['score']:.2f}")
        print(f"   理由：{rec['reason']}")
    
    # 测试场景 3：会话总结
    print('\n【测试 3】会话总结场景')
    context = {
        'keywords': ['总结', '摘要', '回顾', '待办']
    }
    recommendations = recommender.recommend('summary', context, top_k=3)
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['template']}")
        print(f"   描述：{rec['description']}")
        print(f"   得分：{rec['score']:.2f}")
        print(f"   理由：{rec['reason']}")
    
    print('\n' + '=' * 60)


if __name__ == '__main__':
    main()
