# -*- coding: utf-8 -*-
"""沙坪坝教培合并到master并去重"""
import sys, os, csv, re
sys.stdout.reconfigure(encoding='utf-8')

master_csv = 'data/master/jp_list_chongqing_latest.csv'
spb_names = 'data/source/weijkw/jp_chongqing_shapingba_names.txt'

# 读取现有master
master_rows = []
with open(master_csv, encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    master_rows = list(reader)
    headers = reader.fieldnames

print(f"master教培现有: {len(master_rows)}家")

# 读取沙坪坝名称
with open(spb_names, encoding='utf-8') as f:
    spb_names_list = [l.strip() for l in f if l.strip()]
print(f"沙坪坝新增: {len(spb_names_list)}家")

# 现有master中已存在的名称（含变体）用于去重
existing_names = set()
for r in master_rows:
    existing_names.add(r['机构名称'])

# 归一化函数：去空格、全半角、去"重庆""渝"前后缀差异辅助匹配
def norm(name):
    n = name.replace(' ', '').replace('（', '(').replace('）', ')')
    n = re.sub(r'有限公司|有限责任公司|公司$', '', n)
    n = n.replace('重庆市沙坪坝区', '').replace('重庆沙坪坝', '').replace('重庆市', '').replace('重庆', '')
    return n

existing_norm = {norm(n) for n in existing_names if n}

# 去重：沙坪坝机构若核心名已在master则跳过
added = 0
skipped = 0
for name in spb_names_list:
    if not name:
        continue
    if norm(name) in existing_norm:
        skipped += 1
        continue
    # 新增
    master_rows.append({
        '区域': '沙坪坝区',
        '机构名称': name,
        '地址': '',
        '电话': '',
        '机构类别': '培训机构',
        'adname': '沙坪坝区',
        '经度': '',
        '纬度': '',
        '数据来源': '沙坪坝区教委白名单(2025.09)',
        '抓取时间': '2026-08-29'
    })
    existing_norm.add(norm(name))
    added += 1

print(f"新增: {added}家, 跳过已存在: {skipped}家")

# 写回master
with open(master_csv, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writeheader()
    writer.writerows(master_rows)

print(f"合并后 master教培: {len(master_rows)}家")