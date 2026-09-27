# -*- coding: utf-8 -*-
"""光伏获客系统 - 分析报告生成器"""
import sys, os
from pathlib import Path
BASE = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE / "scripts"))
os.chdir(str(BASE))

from core.database import PVDatabase

db = PVDatabase()

print("=" * 55)
print("📊 光伏获客系统 — 完整报告")
print("=" * 55)

# 1. 政策分析
print("\n📜 最新光伏政策 (15条)")
for p in db.get_latest_policies(10):
    print(f"  [{p['level']}] {p['title'][:45]}")

# 2. 热点分析
print("\n🔥 光伏热点 (今日)")
analysis = db.get_pv_analysis()
print(f"  政策库: {analysis['policy_count']} 条")
print(f"  竞品库: {analysis['competitor_count']} 家")

# 3. 推荐内容方向
print("\n💡 内容方向推荐")
directions = [
    ("政策解读", "2026年户用光伏补贴新政：0.03元/度，7步搞定并网", "用户想省钱装光伏，关心补贴和流程"),
    ("收益计算", "安装5KW光伏到底能赚多少钱？算笔账给你看", "自建房业主最关心的ROI问题"),
    ("避坑指南", "光伏安装3大坑，90%的人踩过，第2个最致命", "降低决策阻力，建立信任"),
    ("行业新闻", "山东的今天是很多省的明天：分布式光伏新规解读", "针对工商业老板的政策焦虑"),
    ("技术科普", "四可改造是什么？你的光伏电站必须升级了", "技术向内容，建立专业形象"),
]
for name, title, reason in directions:
    print(f"  [{name}] {title[:40]}")
    print(f"       目标: {reason}")

# 4. 区域分析
print("\n🌍 重点区域推荐")
regions = [
    ("浙江", "省补0.02元/kWh，AGC必配，截止2026年6月"),
    ("广东", "大湾区部分城市有补贴，南网认证要求"),
    ("江苏", "苏北部分地市有补贴，整县推进"),
    ("山东", "无省级补贴，但电网承载压力大"),
    ("河南", "红色预警区域暂停备案，需谨慎"),
]
for prov, note in regions:
    print(f"  {prov}: {note}")

db.close()
print("\n" + "=" * 55)