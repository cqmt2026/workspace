# -*- coding: utf-8 -*-
"""
Agent 调度器增强
支持意图识别和任务分发
"""

import re
from typing import Optional, Dict

class AgentDispatcher:
    """Agent 调度器"""
    
    def __init__(self):
        self.intent_patterns = self._load_intent_patterns()
    
    def _load_intent_patterns(self) -> Dict:
        """加载意图识别模式"""
        return {
            'edit': [
                r'编辑.*章',
                r'修改.*章',
                r'调整.*章',
                r'改写.*章',
            ],
            'optimize': [
                r'优化.*章',
                r'润色.*章',
                r'提升.*章',
                r'改进.*章',
            ],
            'review': [
                r'审核.*章',
                r'检查.*章',
                r'评估.*章',
                r'质检.*章',
            ],
            'create': [
                r'创作.*章',
                r'写.*章',
                r'生成.*章',
                r'第.*章',  # 匹配"第 52 章"
            ],
            'novel': [  # 小说相关
                r'小说',
                r'陆鸣',
                r'鉴城师',
            ],
            'social': [  # 自媒体相关
                r'小红书',
                r'公众号',
                r'抖音',
                r'自媒体',
            ],
            'investment': [  # 投资相关
                r'股票',
                r'基金',
                r'茅台',
                r'分析',
                r'投资',
            ],
        }
    
    def is_novel_edit_request(self, message: str) -> bool:
        """检测编辑请求"""
        return self._match_intent(message, 'edit')
    
    def is_novel_optimize_request(self, message: str) -> bool:
        """检测优化请求"""
        return self._match_intent(message, 'optimize')
    
    def is_novel_review_request(self, message: str) -> bool:
        """检测审核请求"""
        return self._match_intent(message, 'review')
    
    def is_novel_create_request(self, message: str) -> bool:
        """检测创作请求"""
        return self._match_intent(message, 'create')
    
    def _match_intent(self, message: str, intent: str) -> bool:
        """匹配意图"""
        patterns = self.intent_patterns.get(intent, [])
        for pattern in patterns:
            if re.search(pattern, message):
                return True
        return False
    
    def dispatch(self, message: str) -> Optional[str]:
        """分派任务到对应 Agent"""
        # 先检查具体任务类型
        if self.is_novel_edit_request(message):
            return 'novel'
        elif self.is_novel_optimize_request(message):
            return 'novel'
        elif self.is_novel_review_request(message):
            return 'novel'
        elif self.is_novel_create_request(message):
            return 'novel'
        # 再检查领域
        elif self._match_intent(message, 'novel'):
            return 'novel'
        elif self._match_intent(message, 'social'):
            return 'social'
        elif self._match_intent(message, 'investment'):
            return 'investment'
        return None


# 测试
if __name__ == '__main__':
    dispatcher = AgentDispatcher()
    
    test_cases = [
        ('编辑第 50 章', 'edit'),
        ('优化第 51 章', 'optimize'),
        ('审核第 52 章', 'review'),
        ('创作第 53 章', 'create'),
        ('今天天气不错', None),
    ]
    
    print('=== 意图识别测试 ===')
    for message, expected in test_cases:
        result = dispatcher.dispatch(message)
        status = '[OK]' if result == expected else '[FAIL]'
        print(f'{status} "{message}" -> {result} (expected: {expected})')
