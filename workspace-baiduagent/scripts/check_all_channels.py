# -*- coding: utf-8 -*-
"""完整盘点所有渠道的数据覆盖情况"""
import sqlite3, csv, os, sys
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
MASTER_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\master'
SOURCE_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\source'

print("=" * 78)
print("【多渠道数据覆盖全景盘点】")
print("=" * 78)

# ========== 1. CRM行业覆盖率 ==========
print("\n📊 一、CRM已覆盖行业及电话覆盖率")
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute('''
    SELECT industry, COUNT(*) as total,
           SUM(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 ELSE 0 END) as has_phone,
           SUM(CASE WHEN source LIKE '%高德%' OR source LIKE '%百度%' OR source LIKE '%腾讯%' 
                    OR source LIKE '%卫健委%' OR source LIKE '%教委%' OR source LIKE '%住建委%'
                    OR source LIKE '%专精特新%' THEN 1 ELSE 0 END) as has_source
    FROM customers GROUP BY industry ORDER BY total DESC
''')
print(f"   {'行业':<14} {'总数':>6} {'有电话':>8} {'覆盖率':>8} {'状态'}")
print("   " + "-" * 52)
for r in cur.fetchall():
    rate = r[2]*100//r[1] if r[1] else 0
    icon = '✅' if rate >= 70 else ('⚠️' if rate >= 50 else '❌')
    print(f"   {r[0]:<14} {r[1]:>6} {r[2]:>8} {rate:>5}% {icon}")
conn.close()

# ========== 2. Source目录全盘点 ==========
print("\n📁 二、Source原始数据渠道盘点")
channels = {}
for subdir in ['amap', 'tencent', 'weijkw', 'gxq', 'jiaowei', 'zjw', 'qcc']:
    subpath = os.path.join(SOURCE_DIR, subdir)
    if not os.path.exists(subpath):
        channels[subdir] = {'rows': 0, 'files': 0}
        continue
    rows = 0
    files = []
    for f in os.listdir(subpath):
        if f.endswith('.csv'):
            with open(os.path.join(subpath, f), encoding='utf-8-sig') as fh:
                rows += sum(1 for _ in fh) - 1
            files.append(f)
    channels[subdir] = {'rows': rows, 'files': len(files)}
    if rows > 0:
        print(f"   {subdir}/: {rows:,}行 ({len(files)}个文件)")

# ========== 3. Master文件分类 ==========
print("\n📂 三、Master文件渠道归属")
masters = {'高德POI': [], '百度POI': [], '官方名单': [], '其他': []}
for f in sorted(os.listdir(MASTER_DIR)):
    if not f.endswith('.csv'):
        continue
    with open(os.path.join(MASTER_DIR, f), encoding='utf-8-sig') as fh:
        rows = sum(1 for _ in fh) - 1
    if rows <= 0:
        continue
    if 'baidu' in f:
        masters['百度POI'].append((f, rows))
    elif 'chongqing_latest' in f:
        masters['高德POI'].append((f, rows))
    elif '_sp' in f or 'tier2' in f or 'jxzb' in f or 'jzjc' in f:
        masters['官方名单'].append((f, rows))
    else:
        masters['其他'].append((f, rows))

for name, items in masters.items():
    if not items:
        continue
    total_rows = sum(r for _, r in items)
    print(f"\n   {name} ({len(items)}个文件, 共{total_rows:,}行):")
    for fname, r in sorted(items, key=lambda x: -x[1])[:5]:
        print(f"     {fname}: {r}行")
    if len(items) > 5:
        print(f"     ... 等{len(items)}个文件")

# ========== 4. 多渠道汇总 ==========
print("\n" + "=" * 78)
print("【多渠道覆盖汇总】")
print("=" * 78)
grand_total = 0
for name, items in masters.items():
    t = sum(r for _, r in items)
    grand_total += t
    print(f"   {name}: {t:,}行")
print(f"   {'合计':>15}: {grand_total:,}行")

# ========== 5. 渠道缺口分析 ==========
print("\n🔍 五、渠道缺口分析（哪些行业缺哪个渠道）")
print("   当前高德为主力，百度为补充，官方为验证")
print("   缺口行业：软件/智能制造/物流/检验检测等电话覆盖率<40%")
print("   缺失渠道：企查查/天眼查（工商全量数据）/市级卫健委/教委")
