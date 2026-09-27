# -*- coding: utf-8 -*-
"""
记忆接入层 v3.2 — 多DB分库 + 质量过滤
每个子系统写入前自动判断价值，避免噪音积累
"""
import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'memory'))

from memory_tools import get_memory_tools

_mt = None

def _get_mt():
    global _mt
    if _mt is None:
        _mt = get_memory_tools()
    return _mt

# ========== 质量过滤器 ==========

# 无意义的模式（匹配即跳过）
JUNK_PATTERNS = [
    r'^写入失败',
    r'^加载失败',
    r'^Supermemory写入失败',
    r'^让我分析',
    r'^脚本路径',
]

# 高价值内容（命中则跳过junk检查）
HIGH_VALUE_PATTERNS = [
    # 踩坑/解决方案
    r'踩坑', r'根因', r'固化措施', r'corrections', r'修复', r'解决', r'方案',
    # 升级/系统改进
    r'升级', r'迁移', r'改造', r'优化', r'重构', r'部署', r'接入', r'闭环',
    # 专业知识（各领域）
    r'专业知识', r'知识点', r'定义', r'核心要点', r'公式', r'标准',
    r'验房', r'容积率', r'改造', r'开发流程',
    r'策略', r'信号', r'涨停', r'RPS', r'板块', r'大盘', r'市场',
    r'爆款', r'热点', r'抖音', r'播放', r'粉丝',
    # 角色/设定/创作
    r'角色', r'设定', r'世界观', r'情节', r'人物', r'陆鸣',
    # 决策/重要事件
    r'决策', r'决定', r'完成', r'成功',
    # 视频内容提取
    r'视频', r'转写', r'转录', r'内容提取',
    # 通用高价值
    r'系统', r'知识', r'报告', r'总结', r'学习', r'参考',
]

MIN_LENGTH = 20

def _is_junk(text):
    # 高价值内容直接通过（不限长度）
    for p in HIGH_VALUE_PATTERNS:
        if re.search(p, text):
            return False
    if len(text) < MIN_LENGTH:
        return True
    for p in JUNK_PATTERNS:
        if re.search(p, text):
            return True
    return False

# ========== 核心接口 ==========

def save(content, category='general', entities=None, source=None, domain=None):
    if _is_junk(content):
        return {'success': False, 'note': 'filtered', 'text': content[:40]}
    return _get_mt().save_memory(
        content, category=category,
        entities=entities or [], source=source, domain=domain
    )

def search(query, top_k=10, category=None, domain=None):
    return _get_mt().search_memory(query, top_k=top_k, category=category, domain=domain)

# ========== 子系统专用接口 ==========

def save_plot(text, source='novel'):
    return save(text, category='plot', source=source, domain='novel')

def save_character(name, description, source='novel'):
    return save(description, category='character', entities=[name], source=source, domain='novel')

def save_setting(name, description, source='novel'):
    return save(description, category='setting', entities=[name], source=source, domain='novel')

def save_investment_strategy(text, source='investment'):
    return save(text, category='strategy', source=source, domain='investment')

def save_market_analysis(text, source='investment'):
    return save(text, category='market', source=source, domain='investment')

def save_topic(text, source='social'):
    return save(text, category='topic', source=source, domain='social')

def save_animation(text, source='math'):
    return save(text, category='animation', source=source, domain='math')

def save_decision(text, source='system'):
    return save(text, category='decision', source=source, domain='system')

def save_log(text, source='system-logs'):
    # 日志类特殊处理：只保留有FAIL的记录
    if 'FAIL' not in text and 'error' not in text.lower() and '失败' not in text:
        return {'success': False, 'note': 'filtered: all-OK log'}
    return save(text, category='log', source=source, domain='system')