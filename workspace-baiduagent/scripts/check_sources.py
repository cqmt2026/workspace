# -*- coding: utf-8 -*-
"""检查所有可用的官方/权威数据名单"""
import sys, os, re
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("📂 可用的多渠道数据源盘点")
print("=" * 60)

# 1. 创新型中小企业名单
innov = []
try:
    with open('assets/重庆主城区创新型中小企业_精准版.md', encoding='utf-8') as f:
        content = f.read()
    # 提取企业名（带序号的行）
    for line in content.split('\n'):
        line = line.strip()
        m = re.match(r'^\d+\.\s*(?:\(\d+第二批\)\s*)?(.+)$', line)
        if m and ('有限公司' in line or '科技' in line or '公司' in line):
            innov.append(m.group(1).strip().replace('**',''))
    print(f"1. 主城区创新型中小企业: {len(innov)}家")
except Exception as e:
    print(f"1. 创新型名单读取失败: {e}")

# 2. 专精特新名单
sp = []
try:
    with open('assets/重庆专精特新企业全名单_2275家.md', encoding='utf-8') as f:
        for line in f:
            m = re.match(r'^\d+\.\s+(.+)$', line.strip())
            if m:
                sp.append(m.group(1).strip())
    print(f"2. 专精特新企业: {len(sp)}家")
except Exception as e:
    print(f"2. 专精特新读取失败: {e}")

# 3. 专精特新doc (可解析)
print("3. 专精特新2025名单.doc: 存在(备用)")

# 4. 中小企业申报/创新型其他批次
print("4. 其他官方名单: 待查")

# 对比去重
print(f"\n专精特新 + 创新型部分重叠，可用企查查补电话")