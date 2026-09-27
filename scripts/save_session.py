# -*- coding: utf-8 -*-
"""
会话保存脚本 — 将当前会话的关键讨论写入记忆库
在会话结束时由主系统调用，自动提取有价值内容持久化
"""
import sys, os, json, re
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'memory'))
from memory_tools import get_memory_tools

_mt = None
def _get_mt():
    global _mt
    if _mt is None:
        _mt = get_memory_tools()
    return _mt

# 价值内容关键词 — 命中即保存
VALUE_PATTERNS = [
    r'(踩坑|根因|固化措施|修复|解决方案)',
    r'(升级|迁移|改造|优化|重构|部署|接入|闭环)',
    r'(专业|知识点|核心要点|公式|标准)',
    r'(策略|信号|涨停|RPS|板块|大盘|市场)',
    r'(爆款|热点|抖音|播放|粉丝)',
    r'(角色|设定|世界观|情节|人物)',
    r'(决策|决定|完成|成功)',
    r'(联通|拓客|线上获客|异业合作|精准投放)',
    r'(分析|方案|策划|调研|竞品)',
]

# 无意义模式 — 跳过
JUNK_PATTERNS = [
    r'^(好的|好的吧|嗯|哦|对|是|行|好|可以|明白|知道)',
    r'^(早上好|晚上好|下午好|晚安|早|嗨)',
    r'^(谢谢|感谢|收到|了解)',
    r'^(稍等|等一下|让我)',
]

def _is_valuable(text):
    """判断是否为有价值内容"""
    if len(text) < 30:
        return False
    for p in JUNK_PATTERNS:
        if re.match(p, text):
            return False
    for p in VALUE_PATTERNS:
        if re.search(p, text):
            return True
    return False

def _extract_key_topics(text):
    """提取关键词标签"""
    topics = []
    # 常见话题词
    topic_patterns = [
        (r'(联通|电信|移动|运营商)', '通信'),
        (r'(拓客|获客|拉新|引流|线上获客)', '获客'),
        (r'(抖音|快手|视频号|小红书|B站)', '短视频'),
        (r'(微信|公众号|企微|社群|私域)', '微信生态'),
        (r'(小说|番茄|网文|创作|写作)', '小说'),
        (r'(股票|涨停|投资|策略|板块|大盘)', '投资'),
        (r'(自媒体|爆款|热点|内容创作)', '自媒体'),
        (r'(数学动画|manim|可视化)', '数学动画'),
        (r'(小程序|微信小程序|前端)', '小程序'),
        (r'(升级|迁移|部署|架构)', '系统'),
        (r'(踩坑|修复|bug|错误)', '踩坑'),
    ]
    for pattern, topic in topic_patterns:
        if re.search(pattern, text):
            if topic not in topics:
                topics.append(topic)
    return topics

def save_session_discussion(title, messages, source='main-session'):
    """
    保存会话讨论到记忆库
    title: 会话主题摘要
    messages: 对话内容列表 [{'role': 'user'|'assistant', 'content': str}, ...]
    """
    # 提取有价值的对话轮次
    valuable_pairs = []
    current_topic = None
    
    for i, msg in enumerate(messages):
        text = msg.get('content', '').strip()
        if not text:
            continue
        
        if not _is_valuable(text):
            continue
        
        # 提取话题标签
        topics = _extract_key_topics(text)
        
        # 构建保存内容
        entry = {
            'text': text,
            'role': msg.get('role', 'unknown'),
            'topics': topics,
        }
        valuable_pairs.append(entry)
    
    if not valuable_pairs:
        return {'saved': 0, 'note': 'no valuable content found'}
    
    # 合并相关对话为完整讨论块
    saved_count = 0
    discussions = []
    current_block = []
    current_topics = set()
    
    for entry in valuable_pairs:
        current_block.append(entry['text'])
        current_topics.update(entry['topics'])
        
        # 每3轮或遇到主题变化时打包
        if len(current_block) >= 3:
            discussions.append({
                'text': '\n'.join(current_block),
                'topics': list(current_topics),
            })
            current_block = []
            current_topics = set()
    
    # 最后剩余的内容
    if current_block:
        discussions.append({
            'text': '\n'.join(current_block),
            'topics': list(current_topics),
        })
    
    # 写入记忆库
    mt = _get_mt()
    today = datetime.now().strftime('%Y-%m-%d')
    
    for disc in discussions:
        content = f"[{today}] {title}\n{disc['text']}"
        category = 'conversation'
        
        result = mt.save_memory(
            text=content,
            category=category,
            entities=disc['topics'],
            session_id=source,
            agent_id='main',
            source='main-session',
            domain='system',
        )
        if result.get('success'):
            saved_count += 1
    
    return {
        'saved': saved_count,
        'total_pairs': len(valuable_pairs),
        'topics': list(set(t for d in discussions for t in d['topics'])),
        'note': 'saved to memory_system.db',
    }

def save_conversation_summary(title, summary_text, topics=None):
    """直接保存一个会话摘要（由主系统调用）"""
    mt = _get_mt()
    today = datetime.now().strftime('%Y-%m-%d')
    content = f"[{today}] {title}\n{summary_text}"
    
    result = mt.save_memory(
        text=content,
        category='conversation',
        entities=topics or [],
        session_id='main-session',
        agent_id='main',
        source='main-session',
        domain='system',
    )
    return result


if __name__ == '__main__':
    # 测试
    test_messages = [
        {'role': 'user', 'content': '重庆联通城区线上拓客有什么好方案？'},
        {'role': 'assistant', 'content': '可以从抖音本地推、微信社群、异业合作几个方向切入...'},
        {'role': 'user', 'content': '具体说说抖音本地推怎么搞'},
    ]
    result = save_session_discussion('重庆联通线上拓客讨论', test_messages)
    print(json.dumps(result, ensure_ascii=False, indent=2))