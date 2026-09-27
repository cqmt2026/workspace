#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""GitHub Trending 数据采集脚本（API版）"""
import urllib.request
import json
import sys
import os
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = r"C:\Users\Administrator\.openclaw\workspace"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def fetch_api(query, per_page=10):
    """GitHub Search API 查询"""
    url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page={per_page}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"[ERROR] API请求失败: {e}")
        return None

def get_trending_today():
    """获取今日热门（近7天创建，按星标排序）"""
    return fetch_api("created:>2026-08-24")

def get_python_trending():
    """获取Python专场"""
    return fetch_api("language:python created:>2026-08-24")

def get_new_today():
    """获取今日新增（24小时内）"""
    return fetch_api("created:>2026-08-30")

def format_item(item, idx):
    """格式化单个项目"""
    name = item['full_name']
    desc = item.get('description', '') or '无描述'
    stars = item.get('stargazers_count', 0)
    lang = item.get('language', 'N/A') or 'N/A'
    created = item['created_at'][:10]
    url = item['html_url']
    
    # 截断描述
    desc_short = desc[:70] + '...' if len(desc) > 70 else desc
    
    lines = [
        f"  {idx}. **{name}** ⭐{stars:,}",
        f"     📝 {desc_short}",
        f"     🔤 {lang} | 📅 {created}",
        f"     🔗 {url}",
        ""
    ]
    return '\n'.join(lines)

def build_report():
    """构建完整报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    print("[INFO] 正在获取 GitHub Trending 数据...")
    
    # 获取数据
    today_data = get_trending_today()
    python_data = get_python_trending()
    new_data = get_new_today()
    
    if not today_data or not today_data.get('items'):
        print("[ERROR] 无法获取数据")
        return None
    
    items = today_data['items']
    python_items = python_data.get('items', []) if python_data else []
    new_items = new_data.get('items', []) if new_data else []
    
    # 构建报告
    lines = [
        f"# GitHub Trending 每日追踪 | {now}（周一）",
        "",
        "> 数据来源：GitHub Search API（GitHub 主站被墙，改用 API 数据源）",
        "",
        "---",
        "",
        "## 📊 今日概览（近7日热门）",
        "",
        f"**共发现 {len(items)} 个热门项目**（按星标排序）",
        "",
        "### 🔥 全语言 TOP 10",
        "",
        "| # | 仓库 | 描述 | ⭐ Star | 语言 | 创建日期 |",
        "|---|------|------|---------|------|---------|",
    ]
    
    for i, item in enumerate(items[:10], 1):
        name = item['full_name']
        desc = (item.get('description') or 'N/A')[:40]
        stars = item.get('stargazers_count', 0)
        lang = item.get('language', 'N/A') or 'N/A'
        created = item['created_at'][:10]
        url = item['html_url']
        lines.append(f"| {i} | [{name}]({url}) | {desc}... | {stars:,} | {lang} | {created} |")
    
    lines.extend([
        "",
        "### 🐍 Python 专场 TOP 10",
        "",
    ])
    
    if python_items:
        lines.extend([
            "| # | 仓库 | 描述 | ⭐ Star | 创建日期 |",
            "|---|------|------|---------|---------|",
        ])
        for i, item in enumerate(python_items[:10], 1):
            name = item['full_name']
            desc = (item.get('description') or 'N/A')[:40]
            stars = item.get('stargazers_count', 0)
            created = item['created_at'][:10]
            url = item['html_url']
            lines.append(f"| {i} | [{name}]({url}) | {desc}... | {stars:,} | {created} |")
    else:
        lines.append("  (暂无Python专场数据)")
    
    lines.extend([
        "",
        "### 🆕 今日新增（2026-08-31）",
        "",
    ])
    
    if new_items:
        lines.extend([
            "| # | 仓库 | 描述 | ⭐ Star |",
            "|---|------|------|---------|",
        ])
        for i, item in enumerate(new_items[:5], 1):
            name = item['full_name']
            desc = (item.get('description') or 'N/A')[:40]
            stars = item.get('stargazers_count', 0)
            url = item['html_url']
            lines.append(f"| {i} | [{name}]({url}) | {desc}... | {stars:,} |")
    else:
        lines.append("  (今日新增较少)")
    
    lines.extend([
        "",
        "---",
        "",
        "## 📈 趋势分析",
        "",
        "### 本周热点方向",
        "",
    ])
    
    # 简单趋势分析
    lang_counts = {}
    for item in items[:20]:
        lang = item.get('language') or 'Other'
        lang_counts[lang] = lang_counts.get(lang, 0) + 1
    
    lines.append("| 语言 | 数量 |")
    lines.append("|------|------|")
    for lang, count in sorted(lang_counts.items(), key=lambda x: -x[1])[:5]:
        lines.append(f"| {lang} | {count} |")
    
    lines.extend([
        "",
        "---",
        "",
        "## 🔧 数据源说明",
        "",
        "**GitHub 主站被墙，已切换为 API 数据源。**",
        "API 通过 curl 可直接访问，数据可靠。",
        "",
        "### API 查询方式",
        "```bash",
        "# 全语言近7天热门",
        'curl "https://api.github.com/search/repositories?q=created:>2026-08-24&sort=stars&order=desc&per_page=10"',
        "",
        "# Python 专场",
        'curl "https://api.github.com/search/repositories?q=language:python+created:>2026-08-24&sort=stars&order=desc&per_page=10"',
        "```",
        "",
        "---",
        "",
        f"*报告由 GitHub Trending 每日追踪脚本自动生成 | 数据源：GitHub Search API*",
        "",
    ])
    
    return '\n'.join(lines)

def main():
    report = build_report()
    
    if not report:
        print("[ERROR] 报告生成失败")
        return 1
    
    # 保存报告
    report_dir = os.path.join(WORKSPACE, "reports")
    os.makedirs(report_dir, exist_ok=True)
    report_file = os.path.join(report_dir, f"github_trending_{datetime.now().strftime('%Y%m%d')}.md")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"[SAVE] 报告已保存至: {report_file}")
    print(f"[SIZE] 文件大小: {os.path.getsize(report_file)} bytes")
    
    # 打印预览
    print("\n" + "="*50)
    print("报告预览（前30行）:")
    print("="*50)
    for line in report.split('\n')[:30]:
        print(line)
    print("...")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
