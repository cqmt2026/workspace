#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""分析百度指数采集结果"""

import csv
import json
import sys
from pathlib import Path
from datetime import datetime

# 设置控制台输出编码为 UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# 读取所有 JSON 文件
data_dir = Path('newrank_data')
results = []

for json_file in sorted(data_dir.glob('baidu_index_*.json'), reverse=True):
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if data.get('status') == 'success':
                keyword = data.get('keyword', '未知')
                trend_index = data.get('trend_index', {})
                avg_index = trend_index.get('avg', 0)
                max_index = trend_index.get('max', 0)
                trend = trend_index.get('trend', 'stable')
                
                results.append({
                    'keyword': keyword,
                    'avg_index': avg_index,
                    'max_index': max_index,
                    'trend': trend,
                    'demand_avg': data.get('demand_index', {}).get('avg', 0),
                    'positive': data.get('public_opinion', {}).get('positive', 0),
                    'neutral': data.get('public_opinion', {}).get('neutral', 0),
                    'negative': data.get('public_opinion', {}).get('negative', 0),
                })
    except Exception as e:
        print(f"Error reading {json_file}: {e}")

# 按平均指数排序
results.sort(key=lambda x: x['avg_index'], reverse=True)

# 输出报告
print("=" * 60)
print("房地产自媒体 - 百度指数采集报告")
print(f"采集时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)
print()

print("[TOP5] 关键词指数排名")
print("-" * 60)
for i, r in enumerate(results[:5], 1):
    trend_mark = "[+]" if r['trend'] == 'rising' else "[=]" if r['trend'] == 'stable' else "[-]"
    print(f"{i}. {r['keyword']}: 平均指数 {r['avg_index']:,} {trend_mark} ({r['trend']})")

print()
print("[趋势] 环比变化分析")
print("-" * 60)
rising = [r for r in results if r['trend'] == 'rising']
stable = [r for r in results if r['trend'] == 'stable']
falling = [r for r in results if r['trend'] == 'falling']

print(f"上升：{len(rising)} 个关键词 ({', '.join([r['keyword'] for r in rising]) if rising else '无'})")
print(f"稳定：{len(stable)} 个关键词 ({', '.join([r['keyword'] for r in stable])})")
print(f"下降：{len(falling)} 个关键词 ({', '.join([r['keyword'] for r in falling]) if falling else '无'})")

print()
print("[建议] 选题方向")
print("-" * 60)

# 基于指数趋势给出选题建议
if rising:
    print("[热点] 上升关键词（建议优先选题）:")
    for r in rising:
        print(f"   - 《{r['keyword']} 最新动向》系列")

print()
print("[常规] 高指数稳定关键词:")
for r in stable[:3]:
    print(f"   - 《{r['keyword']} 深度解析》系列")

print()
print("[舆情] 正面情绪占比较高关键词:")
for r in sorted(results, key=lambda x: x['positive'], reverse=True)[:3]:
    print(f"   - {r['keyword']}: 正面 {r['positive']}%, 中性 {r['neutral']}%, 负面 {r['negative']}%")

print()
print("[策略] 综合建议:")
print("   1. 重点关注上升关键词，结合热点创作")
print("   2. 高指数关键词保持周更频率")
print("   3. 正面情绪高的关键词适合做推荐类内容")
print("   4. 下降关键词可暂时降低优先级")

print()
print("=" * 60)

# 保存汇总报告
report_path = data_dir / f"baidu_index_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
with open(report_path, 'w', encoding='utf-8') as f:
    f.write("# 百度指数采集报告\n\n")
    f.write(f"采集时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    f.write("## TOP5 关键词\n\n")
    for i, r in enumerate(results[:5], 1):
        f.write(f"{i}. {r['keyword']}: {r['avg_index']:,} ({r['trend']})\n")
    f.write("\n## 完整数据\n\n")
    f.write("| 关键词 | 平均指数 | 最高指数 | 趋势 |\n")
    f.write("|--------|----------|----------|------|\n")
    for r in results:
        f.write(f"| {r['keyword']} | {r['avg_index']:,} | {r['max_index']:,} | {r['trend']} |\n")
    f.write("\n## 选题建议\n\n")
    f.write("### 热点上升关键词\n\n")
    if rising:
        for r in rising:
            f.write(f"- 《{r['keyword']} 最新动向》系列\n")
    else:
        f.write("暂无上升关键词\n")
    f.write("\n### 高指数稳定关键词\n\n")
    for r in stable[:3]:
        f.write(f"- 《{r['keyword']} 深度解析》系列\n")

print(f"[文件] 报告已保存：{report_path}")
