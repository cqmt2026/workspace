# -*- coding: utf-8 -*-
"""
自动压缩引擎
智能压缩会话内容，保留关键信息
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# 配置
COMPRESSION_CONFIG = {
    'preserve_ratio': 0.3,  # 保留 30% 关键内容
    'min_length': 100,  # 最少保留 100 字
    'max_length': 1000,  # 最多保留 1000 字
}

# 关键信息关键词
KEYWORDS_PRESERVE = [
    '决定', '决策', '结论', '总结',
    '待办', '任务', '计划', '目标',
    '重要', '注意', '警告', '错误',
    '完成', '成功', '失败', '问题'
]

# 可删除内容关键词
KEYWORDS_REMOVE = [
    '你好', '谢谢', '再见',
    '请问', '能', '可以',
    '嗯', '啊', '哦',
    '好的', '没问题'
]


class CompactEngine:
    """自动压缩引擎"""
    
    def __init__(self):
        self.config = COMPRESSION_CONFIG
    
    def compact(self, content: str, mode: str = 'auto') -> str:
        """
        压缩内容
        
        参数:
            content: 原始内容
            mode: 压缩模式 ('auto' 自动 / 'force' 强制)
        
        返回:
            str: 压缩后的内容
        """
        if not content:
            return ''
        
        # 计算目标长度
        original_length = len(content)
        target_length = int(original_length * self.config['preserve_ratio'])
        target_length = max(self.config['min_length'], min(target_length, self.config['max_length']))
        
        # 提取关键句子
        sentences = self._extract_sentences(content)
        key_sentences = self._filter_key_sentences(sentences, target_length)
        
        # 生成摘要
        summary = '\n'.join(key_sentences)
        
        return summary
    
    def _extract_sentences(self, content: str) -> List[str]:
        """提取句子"""
        # 按行分割
        lines = content.split('\n')
        
        # 过滤空行
        sentences = [line.strip() for line in lines if line.strip()]
        
        return sentences
    
    def _filter_key_sentences(self, sentences: List[str], target_length: int) -> List[str]:
        """过滤关键句子"""
        key_sentences = []
        current_length = 0
        
        # 优先保留包含关键词的句子
        for sentence in sentences:
            # 检查是否包含关键词
            is_key = any(keyword in sentence for keyword in KEYWORDS_PRESERVE)
            is_remove = any(keyword in sentence for keyword in KEYWORDS_REMOVE)
            
            # 关键句子优先保留
            if is_key and not is_remove:
                if current_length + len(sentence) <= target_length:
                    key_sentences.append(sentence)
                    current_length += len(sentence)
        
        # 如果关键句子不足，补充其他句子
        if len(key_sentences) < len(sentences) * 0.3:
            for sentence in sentences:
                if sentence not in key_sentences:
                    if current_length + len(sentence) <= target_length:
                        key_sentences.append(sentence)
                        current_length += len(sentence)
        
        return key_sentences
    
    def compact_with_summary(self, content: str, metadata: Dict = None) -> Dict:
        """
        压缩并生成摘要
        
        参数:
            content: 原始内容
            metadata: 元数据（日期、主题等）
        
        返回:
            dict: 压缩结果
        """
        result = {
            'original_length': len(content),
            'compressed_length': 0,
            'compression_ratio': 0.0,
            'content': '',
            'metadata': metadata or {}
        }
        
        # 压缩内容
        compressed = self.compact(content)
        
        result['content'] = compressed
        result['compressed_length'] = len(compressed)
        result['compression_ratio'] = result['compressed_length'] / result['original_length'] if result['original_length'] > 0 else 0
        
        return result


def compact_session(session_history: List[Dict], mode: str = 'auto') -> str:
    """
    压缩会话历史
    
    参数:
        session_history: 会话历史列表
        mode: 压缩模式
    
    返回:
        str: 压缩后的会话摘要
    """
    engine = CompactEngine()
    
    # 合并会话内容
    content = '\n'.join([
        f"{msg.get('role', 'user')}: {msg.get('content', '')}"
        for msg in session_history
    ])
    
    # 压缩
    summary = engine.compact(content, mode)
    
    return summary


def main():
    """测试函数"""
    print('=' * 60)
    print('自动压缩引擎测试')
    print('=' * 60)
    
    # 测试内容
    test_content = '''
你好，我想写一部小说。
好的，请问是什么题材的小说？
我想写都市男频，主角是验房师。
明白了，主角叫什么名字？
主角叫陆鸣，32 岁，有 12 年验房经验。
好的，我已经记住了。
重要决策：确定小说名为《鉴城师》。
待办事项：完成前 50 章大纲。
计划：每天写 3 章，15 天完成。
谢谢你的帮助！
不客气，有问题随时问我。
再见！
再见！
'''
    
    print(f'\n原始内容长度：{len(test_content)} 字')
    
    # 压缩
    engine = CompactEngine()
    result = engine.compact_with_summary(test_content, {
        'date': '2026-04-05',
        'topic': '小说创作'
    })
    
    print(f"压缩后长度：{result['compressed_length']} 字")
    print(f"压缩率：{result['compression_ratio']*100:.1f}%")
    print(f"\n压缩内容:\n{result['content']}")
    print(f"\n元数据：{result['metadata']}")
    
    print('\n' + '=' * 60)


if __name__ == '__main__':
    main()
