# -*- coding: utf-8 -*-
"""综合评估今日执行进度 + 明日执行计划"""
import sqlite3, csv, os, json, sys
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
MASTER_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\master'
SOURCE_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\source'

print("=" * 78)
print("【多渠道数据获取 - 综合评估与执行计划】")
print(f"评估时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("=" * 78)

# ========== 1. 今日已完成 ==========
print("\n📊 一、今日已完成数据获取")
print("-" * 78)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 高德数据
cur.execute("SELECT COUNT(*) FROM customers WHERE source LIKE '%高德%'")
gaode = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM customers WHERE source LIKE '%百度%'")
baidu = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM customers WHERE source LIKE '%卫健委%' OR source LIKE '%weijkw%'")
weijkw = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM customers WHERE source LIKE '%教委%'")
jiaow = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM customers WHERE source LIKE '%住建委%'")
zjw = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM customers WHERE source LIKE '%专精特新%' OR source LIKE '%sp%'")
zhuanjing = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM customers WHERE source LIKE '%创新型%' OR source LIKE '%经信委%'")
jxw = cur.fetchone()[0]

print(f"   高德POI:       {gaode:>5}家 (12个行业)")
print(f"   百度POI:       {baidu:>5}家 (17个行业)")
print(f"   卫健委名单:     {weijkw:>5}家 (3个行业)")
print(f"   教委白名单:     {jiaow:>5}家 (1个行业)")
print(f"   住建委资质:     {zjw:>5}家 (2个行业)")
print(f"   专精特新名单:    {zhuanjing:>5}家 (6个行业)")
print(f"   创新型中小企业:   {jxw:>5}家 (经信委)")
print(f"   {'─' * 50}")
print(f"   合计:           {gaode+baidu+weijkw+jiaow+zjw+zhuanjing+jxw:>5}家")

cur.execute('SELECT COUNT(*) FROM customers')
total = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM customers WHERE phone IS NOT NULL AND phone != ''")
has_tel = cur.fetchone()[0]
print(f"\n   CRM总客户: {total:,}家")
print(f"   有电话: {has_tel:,}家 ({has_tel*100//total}%)")
conn.close()

# ========== 2. 今日渠道配额状态 ==========
print("\n📊 二、三大地图API配额状态")
print("-" * 78)
import requests
GD_KEY = '3f85cf676f4eb0ccb2374560bb99bd51'
r = requests.get('https://restapi.amap.com/v3/place/text',
    params={'keywords': '口腔', 'city': '重庆', 'offset': 5, 'page': 1, 'key': GD_KEY}, timeout=10)
d = r.json()
print(f"   高德: status={d.get('status')}, info={d.get('info')}")

BD_KEY = 'KKcT6s…i2C0'
r2 = requests.get('https://api.map.baidu.com/place/v2/search',
    params={'query': '口腔', 'region': '重庆', 'output': 'json', 'ak': BD_KEY, 'page_size': 3, 'scope': 2}, timeout=10)
d2 = r2.json()
print(f"   百度: status={d2.get('status')}, msg={d2.get('message','')}")

TX_KEY = 'JGGBZ-D5I6Q-66H5K-22SMU-I5VXO-NDFLJ'
r3 = requests.get('https://apis.map.qq.com/ws/place/v1/search',
    params={'key': TX_KEY, 'boundary': 'region(重庆,0)', 'keyword': '口腔', 'max_per_page': 3}, timeout=10)
d3 = r3.json()
print(f"   腾讯: status={d3.get('status')}, msg={d3.get('message','')}")

# ========== 3. 低覆盖率行业分析 ==========
print("\n📊 三、低覆盖率行业（需优先补充电话）")
print("-" * 78)
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("""
    SELECT industry, COUNT(*) as total,
           SUM(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 ELSE 0 END) as has_phone
    FROM customers GROUP BY industry 
    ORDER BY has_phone*100/COUNT(*) ASC
    LIMIT 10
""")
print(f"   {'行业':<14} {'总数':>6} {'有电话':>8} {'覆盖率':>8}")
print("   " + "-" * 42)
for r in cur.fetchall():
    rate = r[2]*100//r[1] if r[1] else 0
    print(f"   {r[0]:<14} {r[1]:>6} {r[2]:>8} {rate:>5}%")
conn.close()

# ========== 4. 渠道缺口分析 ==========
print("\n📊 四、渠道缺口分析")
print("-" * 78)
channels = {
    '高德POI': gaode,
    '百度POI': baidu,
    '卫健委': weijkw,
    '教委': jiaow,
    '住建委': zjw,
    '专精特新': zhuanjing,
    '创新型中小企业': jxw,
    '市场监管局': 0,
    '药监局': 0,
    '交通局': 0,
    '人社局': 0,
    '企查查': 0,
}
for name, cnt in channels.items():
    icon = '✅' if cnt > 0 else '❌'
    print(f"   {icon} {name}: {cnt}家")

# ========== 5. 明日执行计划 ==========
print("\n📋 五、明日执行计划（配额恢复后）")
print("-" * 78)
print("   P0 (立即执行):")
print("     1. 高德POI - 补抓P0/P1低覆盖率行业")
print("     2. 腾讯POI - 重新运行（Key已修复）")
print("     3. 市场监管 - 检验检测/食品/广告资质名单")
print()
print("   P1 (本周内):")
print("     4. 药监局 - 医疗器械生产/经营许可证")
print("     5. 交通局 - 道路运输经营许可")
print("     6. 经信委 - 高新技术企业名单")
print()
print("   P2 (本月):")
print("     7. 企查查/天眼查 - 授权后接入")
print("     8. 行业协会 - 逐一联系获取会员名单")
print()
print("   技术手段:")
print("     - 市场监管局/药监局等动态网页 → 需浏览器自动化")
print("     - 已下载经信委Excel → 可立即解析入库")
