# -*- coding: utf-8 -*-
"""建立数据获取节点清单：盘点已覆盖行业 + 各来源明细，避免重复/遗漏"""
import sqlite3, csv, os, sys
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
MASTER_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\master'
SOURCE_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\source'

print("=" * 78)
print("【数据获取节点清单】- 建立基准，避免重复/遗漏")
print("=" * 78)

# ========== 1. CRM行业分布（已覆盖） ==========
print("\n📊 一、CRM已覆盖行业（当前master全量）")
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute('SELECT industry, COUNT(*) FROM customers GROUP BY industry ORDER BY COUNT(*) DESC')
crm_rows = cur.fetchall()
print(f"   {'行业':<14} {'CRM数量':>8}  状态")
print("   " + "-" * 42)
for industry, cnt in crm_rows:
    print(f"   {industry:<14} {cnt:>8}  ✅已入库")
conn.close()

# ========== 2. Master文件明细 ==========
print("\n📊 二、Master文件（每文件的行业归属）")
master_detail = {}
for f in sorted(os.listdir(MASTER_DIR)):
    if not f.endswith('.csv'):
        continue
    fpath = os.path.join(MASTER_DIR, f)
    with open(fpath, encoding='utf-8-sig') as fh:
        rows = sum(1 for _ in fh) - 1
    if rows <= 0:
        continue
    # 推断行业
    if '_baidu' in f:
        src = '百度'
    elif 'chongqing_latest' in f:
        src = '高德'
    else:
        src = '其他'
    master_detail[f] = {'rows': rows, 'src': src}
    print(f"   {f}: {rows}行 [{src}]")

# ========== 3. 各平台已获取规模 ==========
print("\n📊 三、各平台数据获取规模")
baidu_rows = sum(v['rows'] for v in master_detail.values() if v['src']=='百度')
amap_rows = sum(v['rows'] for v in master_detail.values() if v['src']=='高德')
other_rows = sum(v['rows'] for v in master_detail.values() if v['src']=='其他')
print(f"   百度源: {baidu_rows}行")
print(f"   高德源: {amap_rows}行")
print(f"   其他源: {other_rows}行")
print(f"   合计: {baidu_rows+amap_rows+other_rows}行")

# ========== 4. 配额消耗评估 ==========
print("\n⏰ 四、配额节点管理策略")
print("   - 高德30万/天, 百度5万/天, 腾讯5千/天")
print("   - 三平台共享IP，但配额独立计算")
print("   - 建议抓取策略：高德主力(配额最大) + 百度补充 + 腾讯补漏")

# ========== 5. 去重策略 ==========
print("\n🔁 五、去重策略（避免重复入库）")
print("   1. 按企业名去重（去除同名不同源）")
print("   2. 按电话去重（同一电话多平台）")
print("   3. master为唯一标准，source为原始备份")
print("   4. 新数据先比对CRM已有name+phone")

print("\n" + "=" * 78)
print("【节点基准已建立】下次抓取前先比对此清单")
print("=" * 78)
