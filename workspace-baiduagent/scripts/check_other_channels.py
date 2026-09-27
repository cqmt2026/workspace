# -*- coding: utf-8 -*-
"""盘点所有非地图渠道（政府官方/工商/行业等）的数据覆盖情况"""
import os, sys, csv
sys.stdout.reconfigure(encoding='utf-8')

SOURCE_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\source'
MASTER_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\master'

print("=" * 70)
print("【非地图渠道数据盘点】")
print("=" * 70)

# 1. Source目录结构
print("\n📁 Source原始数据目录：")
for subdir in sorted(os.listdir(SOURCE_DIR)):
    subpath = os.path.join(SOURCE_DIR, subdir)
    if not os.path.isdir(subpath):
        continue
    files = os.listdir(subpath)
    csv_files = [f for f in files if f.endswith('.csv')]
    txt_files = [f for f in files if f.endswith('.txt')]
    pdf_files = [f for f in files if f.endswith('.pdf')]
    print(f"  {subdir}/: {len(files)}个文件")
    print(f"    CSV: {len(csv_files)}个, TXT: {len(txt_files)}个, PDF: {len(pdf_files)}个")
    for f in csv_files:
        with open(os.path.join(subpath, f), encoding='utf-8-sig') as fh:
            rows = sum(1 for _ in fh) - 1
        print(f"      {f}: {rows}行")

# 2. Master中非百度/高德/高德latest的文件（官方渠道）
print("\n📊 Master中的官方渠道数据（_sp 后缀 = 专精特新）:")
for f in sorted(os.listdir(MASTER_DIR)):
    if not f.endswith('.csv'):
        continue
    if '_sp' in f or 'tier2_all' in f:
        with open(os.path.join(MASTER_DIR, f), encoding='utf-8-sig') as fh:
            rows = sum(1 for _ in fh) - 1
        print(f"  {f}: {rows}行")

# 3. 官方渠道明细
print("\n📋 官方数据源覆盖情况：")
official = {
    '卫健委(医疗类)': ['weijkw'],
    '高新区(gxq)': ['gxq'],
    '专精特新(工信部)': ['tier2_all_sp'],
    '住建委(装修)': ['装修资质'],
    '教委(教培)': ['教委白名单'],
}
for name, paths in official.items():
    print(f"  {name}: {'待确认' if len(paths)==1 else '待确认'}")

print("\n" + "=" * 70)
print("说明：需补充非地图渠道的详细覆盖清单")
print("=" * 70)
