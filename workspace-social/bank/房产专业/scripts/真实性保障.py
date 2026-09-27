#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
真实性保障模块 V1.0
确保房地产自媒体内容客观、真实、可查证

核心原则（不可更改）：
1. 客观公正，不夸大其词
2. 不虚构事实
3. 数据必须有据可查
4. 优先使用官方/权威机构数据

作者：小智
版本：V1.0
创建时间：2026-03-25
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import re

from logger import logger


class AuthenticityChecker:
    """
    真实性检查器
    
    检查内容是否：
    1. 客观公正（无夸大）
    2. 数据真实（有来源）
    3. 不虚构事实
    """
    
    def __init__(self):
        # 权威数据源白名单（只允许这些来源）
        self.authorized_sources = [
            # 政府机构 - 国家部委
            '国家统计局', '住建部', '自然资源部', '中国人民银行', '央行',
            '银保监会', '银监会', '证监会', '财政部', '发改委',
            
            # 政府机构 - 重庆市级
            '重庆市住建委', '重庆市规划和自然资源局', '重庆市规划委', '重庆市统计局',
            '重庆市发改委', '重庆市财政局',
            
            # 专业机构（全国）
            '克而瑞', '中指研究院', '易居研究院', '戴德梁行',
            '仲量联行', '世邦魏理仕', '高力国际',
            
            # 专业机构（区域/重庆）
            '克而瑞重庆', '中指院西南', '铭腾机构', '重庆锐理数据',
            
            # 上市房企公告（官方披露渠道）
            '万科', '保利发展', '中海地产', '华润置地', '招商蛇口',
            '龙湖集团', '金地集团', '碧桂园', '恒大', '融创',
            '绿城中国', '世茂集团', '旭辉集团', '金科股份', '龙湖',
            '万科 A', '保利地产',
            
            # 官方媒体
            '新华社', '人民日报', '央视新闻', '经济日报',
            '重庆日报', '重庆晨报', '华龙网',
            
            # 正规媒体
            '财经', '财新', '21 世纪经济报道', '第一财经',
            '澎湃新闻', '界面新闻',
        ]
        
        # 上市房企公告使用规范
        self.property_company_announcements = {
            '万科': ['万科 A', '万科企业股份有限公司'],
            '保利发展': ['保利地产', '保利发展控股'],
            '龙湖集团': ['龙湖', '龙湖地产'],
            '中海地产': ['中国海外发展'],
            '华润置地': ['华润置地'],
            '招商蛇口': ['招商局蛇口工业区控股'],
            '金地集团': ['金地'],
            '碧桂园': ['碧桂园控股'],
            '融创': ['融创中国'],
            '金科股份': ['金科'],
        }
        
        # 禁止的夸大词汇
        prohibited_exaggerations = [
            '暴涨', '暴跌', '疯涨', '崩盘', '血亏', '必涨', '稳赚',
            '100%', '绝对', '肯定', '一定', '百分百', '最', '第一',
            '史上', '空前', '绝后', '唯一', '首个', '惊天', '重磅',
            '刚刚曝光', '刚刚传来', '速看', '马上删', '内部消息',
        ]
        
        # 需要标注来源的关键词
        source_required_keywords = [
            '数据显示', '据统计', '报告显示', '调研表明',
            '占比', '同比', '环比', '增长率', '下降', '上涨',
            '成交', '均价', '库存', '去化', '溢价率',
        ]
        
        logger.info("真实性保障模块 V1.0 初始化完成")
    
    def check_article(self, content: str, title: str = '') -> Dict:
        """
        检查文章真实性
        
        Args:
            content: 文章内容
            title: 标题
        
        Returns:
            检查结果
        """
        logger.info("开始真实性检查")
        
        result = {
            'passed': True,
            'score': 100,
            'issues': [],
            'warnings': [],
            'data_claims': [],
            'sources_used': []
        }
        
        # 1. 检查夸大词汇
        exaggeration_issues = self._check_exaggerations(content, title)
        result['issues'].extend(exaggeration_issues)
        result['score'] -= len(exaggeration_issues) * 5
        
        # 2. 检查数据是否有来源
        source_issues = self._check_data_sources(content)
        result['warnings'].extend(source_issues)
        result['score'] -= len(source_issues) * 3
        
        # 3. 检查来源是否权威
        source_quality = self._check_source_authority(content)
        result['sources_used'] = source_quality['sources']
        if not source_quality['has_authority'] and source_quality['has_data']:
            result['issues'].append({
                'type': '数据来源不权威',
                'message': '文章包含数据但未引用权威来源',
                'severity': 'high'
            })
            result['score'] -= 20
        
        # 4. 检查绝对化表述
        absolute_issues = self._check_absolute_statements(content)
        result['issues'].extend(absolute_issues)
        result['score'] -= len(absolute_issues) * 5
        
        # 5. 检查标题是否夸大
        title_issues = self._check_title(title)
        result['issues'].extend(title_issues)
        result['score'] -= len(title_issues) * 10
        
        # 确保分数在合理范围
        result['score'] = max(0, min(100, result['score']))
        result['passed'] = result['score'] >= 70 and len([i for i in result['issues'] if i.get('severity') == 'high']) == 0
        
        logger.info(f"真实性检查完成：{'通过' if result['passed'] else '未通过'} ({result['score']}分)")
        return result
    
    def _check_exaggerations(self, content: str, title: str = '') -> List[Dict]:
        """检查夸大词汇"""
        issues = []
        
        for word in self.prohibited_exaggerations:
            if word in content or word in title:
                issues.append({
                    'type': '夸大词汇',
                    'word': word,
                    'message': f'发现夸大词汇："{word}"，建议删除或替换',
                    'severity': 'medium'
                })
        
        return issues
    
    def _check_data_sources(self, content: str) -> List[Dict]:
        """检查数据是否有来源标注"""
        issues = []
        
        # 查找包含数据的句子
        sentences = re.split(r'[。！？!?]', content)
        
        for sentence in sentences:
            # 检查是否包含数据关键词
            has_data_keyword = any(kw in sentence for kw in self.source_required_keywords)
            # 检查是否有来源标注
            has_source = any(source in sentence for source in self.authorized_sources) or \
                        re.search(r'据.*显示|来自.*数据|.*报告', sentence)
            
            # 检查是否有具体数字
            has_number = re.search(r'\d+\.?\d*%|\d+ 万|\d+ 套|\d+ 元', sentence)
            
            if has_data_keyword and has_number and not has_source:
                issues.append({
                    'type': '数据缺少来源',
                    'sentence': sentence[:50] + '...',
                    'message': '包含数据但未标注来源，请补充数据来源（如：据克而瑞数据显示）',
                    'severity': 'medium'
                })
        
        return issues
    
    def _check_source_authority(self, content: str) -> Dict:
        """检查来源是否权威"""
        result = {
            'sources': [],
            'has_authority': False,
            'has_data': False
        }
        
        # 检查是否使用了权威来源
        for source in self.authorized_sources:
            if source in content:
                result['sources'].append(source)
                result['has_authority'] = True
        
        # 检查是否包含数据
        if re.search(r'\d+\.?\d*%|\d+ 万|\d+ 套|\d+ 元|同比|环比', content):
            result['has_data'] = True
        
        return result
    
    def _check_absolute_statements(self, content: str) -> List[Dict]:
        """检查绝对化表述"""
        issues = []
        
        absolute_patterns = [
            r'一定.*涨', r'肯定.*跌', r'必须.*买', r'千万别.*买',
            r'稳赚.*不赔', r'绝对.*值', r'百分之百.*',
        ]
        
        for pattern in absolute_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                issues.append({
                    'type': '绝对化表述',
                    'pattern': match,
                    'message': f'发现绝对化表述："{match}"，建议改为更客观的表达',
                    'severity': 'high'
                })
        
        return issues
    
    def _check_title(self, title: str) -> List[Dict]:
        """检查标题是否夸大"""
        issues = []
        
        # 标题长度检查
        if len(title) > 35:
            issues.append({
                'type': '标题过长',
                'message': f'标题{len(title)}字，建议控制在 30 字以内',
                'severity': 'low'
            })
        
        # 标题夸大检查
        for word in ['暴涨', '暴跌', '崩盘', '血亏', '惊天', '重磅']:
            if word in title:
                issues.append({
                    'type': '标题夸大',
                    'word': word,
                    'message': f'标题包含夸大词汇："{word}"',
                    'severity': 'high'
                })
        
        return issues
    
    def get_authorized_sources_list(self) -> List[str]:
        """获取权威数据源列表"""
        return self.authorized_sources.copy()
    
    def format_report(self, result: Dict) -> str:
        """格式化检查报告"""
        lines = [
            "真实性检查报告",
            "=" * 50,
            f"检查结果：{'通过' if result['passed'] else '未通过'}",
            f"得分：{result['score']}分",
            ""
        ]
        
        if result['issues']:
            lines.append("【问题列表】")
            for issue in result['issues']:
                severity = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(issue.get('severity', 'low'), '⚪')
                lines.append(f"{severity} {issue.get('type', '问题')}: {issue.get('message', '')}")
            lines.append("")
        
        if result['warnings']:
            lines.append("【警告列表】")
            for warning in result['warnings']:
                lines.append(f"⚠️ {warning.get('message', '')}")
            lines.append("")
        
        if result['sources_used']:
            lines.append("【使用的数据来源】")
            for source in result['sources_used']:
                lines.append(f"✅ {source}")
            lines.append("")
        
        if result['passed']:
            lines.append("✅ 文章符合真实性要求")
        else:
            lines.append("❌ 文章需要修改后才能发布")
        
        return '\n'.join(lines)


# 单例实例
checker = AuthenticityChecker()


def check_authenticity(content: str, title: str = '') -> Dict:
    """快捷检查函数"""
    return checker.check_article(content, title)


def get_authorized_sources() -> List[str]:
    """获取权威数据源列表"""
    return checker.get_authorized_sources_list()


if __name__ == '__main__':
    # 测试
    test_content = """
    重庆房价暴涨，据统计数据显示，上周成交 10000 套，同比上涨 50%。
    专家预测，房价一定还会继续涨，现在不买就买不到了。
    """
    
    test_title = "重庆房价暴涨！专家预测一定还会涨"
    
    result = check_authenticity(test_content, test_title)
    print(checker.format_report(result))
