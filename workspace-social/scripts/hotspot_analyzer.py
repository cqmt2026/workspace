#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
热点采集结果自动分析脚本 V1.0
读取 hotspot_monitor.py 生成的报告，生成 actionable 结论
"""
import io
import os
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

HOTSPOT_DIR = Path(r"C:\Users\Administrator\.openclaw\workspace\workspace-social\memory\热点采集")
ANALYSIS_DIR = Path(r"C:\Users\Administrator\.openclaw\workspace\workspace-social\memory\运营日志\热点分析")

def find_latest_hotspot():
    """找到最新的热点采集报告"""
    if not HOTSPOT_DIR.exists():
        return None
    
    reports = sorted(HOTSPOT_DIR.glob("hotspot_*.md"), reverse=True)
    return reports[0] if reports else None

def parse_hotspot_report(filepath):
    """解析热点报告，提取关键信息"""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # 提取热点列表
    hotspots = []
    for line in content.split('\n'):
        # 匹配格式：- [来源] 标题
        match = re.match(r'\s*-\s*\[([^\]]+)\]\s*(.+)', line)
        if match:
            hotspots.append({
                'source': match.group(1),
                'title': match.group(2)
            })
    
    # 提取选题建议
    suggestions = []
    in_suggestions = False
    for line in content.split('\n'):
        if '选题建议' in line:
            in_suggestions = True
            continue
        if in_suggestions and line.strip().startswith('-'):
            suggestions.append(line.strip()[1:].strip())
    
    return {
        'hotspots': hotspots,
        'suggestions': suggestions,
        'file': str(filepath),
        'date': filepath.stem.replace('hotspot_', '')
    }

def analyze_trends(data):
    """分析热点趋势，生成结论"""
    hotspots = data['hotspots']
    
    # 统计来源分布
    source_count = {}
    for h in hotspots:
        source = h['source']
        source_count[source] = source_count.get(source, 0) + 1
    
    # 提取关键词
    keywords = []
    keyword_count = {}
    for h in hotspots:
        title = h['title']
        # 简单关键词提取（房产相关词）
        for kw in ['重庆', '楼市', '房价', '政策', '购房', '楼盘', '学区', '地铁', '商圈', '土拍']:
            if kw in title:
                keyword_count[kw] = keyword_count.get(kw, 0) + 1
    
    top_keywords = sorted(keyword_count.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        'source_distribution': source_count,
        'top_keywords': top_keywords,
        'total_hotspots': len(hotspots)
    }

def generate_actionable_insights(data, trends):
    """生成可执行的运营建议"""
    insights = []
    
    # 基于关键词的建议
    if trends['top_keywords']:
        top_kw = trends['top_keywords'][0][0]
        insights.append(f"🎯 **内容方向**: 本周热点集中在「{top_kw}」，建议围绕此主题创作 2-3 篇深度内容")
    
    # 基于来源的建议
    if '百度热搜' in trends['source_distribution']:
        insights.append(f"📊 **热度验证**: 百度热搜有 {trends['source_distribution']['百度热搜']} 个房产热点，说明话题具有大众关注度")
    
    # 基于选题建议的建议
    if data['suggestions']:
        insights.append(f"💡 **选题参考**: 已有 {len(data['suggestions'])} 个选题建议，优先执行 S/A 级")
    
    # 时间敏感性建议
    insights.append(f"⏰ **发布时机**: 热点有效期 24-48 小时，建议今天内完成创作并发布")
    
    return insights

def generate_analysis_report(data, trends, insights):
    """生成分析报告"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    content = f"""# 热点采集分析报告

**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**数据源**: {data['file']}
**数据日期**: {data['date']}

---

## 📊 数据概览

| 指标 | 数值 |
|------|------|
| 热点总数 | {trends['total_hotspots']} |
| 来源渠道 | {len(trends['source_distribution'])} |
| 关键词 TOP1 | {trends['top_keywords'][0][0] if trends['top_keywords'] else 'N/A'} |

---

## 🔥 热点来源分布

"""
    for source, count in sorted(trends['source_distribution'].items(), key=lambda x: x[1], reverse=True):
        content += f"- {source}: {count} 个\n"
    
    content += f"""

## 🎯 核心关键词

"""
    for kw, count in trends['top_keywords']:
        content += f"- {kw} ({count}次)\n"
    
    content += f"""

## 💡 可执行建议

"""
    for i, insight in enumerate(insights, 1):
        content += f"{i}. {insight}\n"
    
    content += f"""

## 📝 下一步行动

1. [ ] 从选题建议中选择 1-2 个 S/A 级题目
2. [ ] 查阅 shared-knowledge 中相关方法论
3. [ ] 创作内容并发布
4. [ ] 24 小时后跟踪数据表现

---

_由 可悦🌸 自动生成_
"""
    
    return content

def main():
    print("=" * 60)
    print("热点采集结果自动分析")
    print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 找到最新报告
    latest = find_latest_hotspot()
    if not latest:
        print("[ERROR] 未找到热点采集报告")
        return
    
    print(f"[OK] 找到最新报告：{latest.name}")
    
    # 解析报告
    data = parse_hotspot_report(latest)
    print(f"[OK] 解析完成：{len(data['hotspots'])} 个热点，{len(data['suggestions'])} 个选题建议")
    
    # 分析趋势
    trends = analyze_trends(data)
    print(f"[OK] 趋势分析完成：TOP 关键词 = {trends['top_keywords'][0] if trends['top_keywords'] else 'N/A'}")
    
    # 生成建议
    insights = generate_actionable_insights(data, trends)
    
    # 生成报告
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = ANALYSIS_DIR / f"hotspot_analysis_{datetime.now().strftime('%Y-%m-%d')}.md"
    
    content = generate_analysis_report(data, trends, insights)
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"[OK] 分析报告已生成：{report_file}")
    print("\n核心建议:")
    for insight in insights[:3]:
        print(f"  {insight}")
    
    print("=" * 60)
    
    return str(report_file)

if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    main()
