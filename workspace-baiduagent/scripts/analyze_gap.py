# -*- coding: utf-8 -*-
"""分析第二三梯队数据缺口与多源策略"""
import sys, os, re, csv
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')

# 1. 专精特新名单全部分类（不局限6行业）
print("=" * 60)
print("📌 专精特新2275家名单 - 全行业分类")
print("=" * 60)

INDUSTRY_KWS = {
    '医疗器械': ['医疗','器械','制药','生物制药','医学','医药','药'],
    '新材料化工': ['材料','化工','新材料','塑料','塑胶','胶粘','合金','钛','镁','纤维','节能'],
    '机械装备': ['机械','装备','模具','汽配','汽车零','零部件','起重','液压','传动','机床','金属','铸造','自动化'],
    '环保检测': ['环保','检测','清洁','水处理','净化','环境'],
    '建筑建材': ['建材','装饰','建筑','钢结构','混凝土','保温','幕墙'],
    '新能源': ['新能源','充电','电力','电气','光伏','储能','电池','电网'],
    '软件IT': ['软件','科技','信息','大数据','人工智能','互联网','智能','数字','网络'],
    '食品农业': ['食品','农业','饮料','粮油','农产品','养殖','果品','乳业'],
    '印刷包装': ['印刷','包装','印务','彩印'],
    '纺织服装': ['纺织','服装','服饰','鞋','箱包'],
    '物流仓储': ['物流','仓储','供应链','货运','快递'],
    '汽车整车': ['汽车','机车','摩托','电动车'],
    '电气设备': ['电气','电子','电器','仪器','仪表','机电'],
    '其他': []
}

def classify(name):
    for ind, kws in INDUSTRY_KWS.items():
        for kw in kws:
            if kw in name:
                return ind
    return '其他'

names = []
with open('assets/重庆专精特新企业全名单_2275家.md', encoding='utf-8') as f:
    for line in f:
        m = re.match(r'^\d+\.\s+(.+)$', line.strip())
        if m:
            names.append(m.group(1).strip())

counts = Counter(classify(n) for n in names)
for ind, cnt in counts.most_common():
    print(f"  {ind}: {cnt}家")

# 2. CRM已覆盖的专精特新
print("\n" + "=" * 60)
print("📌 专精特新企业CRM覆盖情况")
print("=" * 60)
import sqlite3
conn = sqlite3.connect('data/baidu_crm.db')
cur = conn.cursor()
covered = set()
cur.execute("SELECT name FROM customers")
for (name,) in cur.fetchall():
    covered.add(name)
conn.close()

matched = [n for n in names if n in covered]
gap = [n for n in names if n not in covered]
print(f"专精特新总数: {len(names)}")
print(f"已在CRM: {len(matched)}家 ({len(matched)/len(names)*100:.0f}%)")
print(f"缺口(未入库): {len(gap)}家")

# 3. 缺口按行业分类
print("\n📌 缺口企业按行业:")
gap_by_ind = Counter(classify(n) for n in gap)
for ind, cnt in gap_by_ind.most_common():
    print(f"  {ind}: {cnt}家")

print("\n📌 缺口示例(非其他类):")
shown = 0
for n in gap:
    if classify(n) != '其他' and shown < 15:
        print(f"  {n} [{classify(n)}]")
        shown += 1