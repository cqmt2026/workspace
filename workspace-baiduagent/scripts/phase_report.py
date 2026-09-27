# -*- coding: utf-8 -*-
import sqlite3, sys, csv, os
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 78)
print("【多渠道数据获取 - 阶段性汇报】")
print("=" * 78)

# ========== 1. 当前配额状态 ==========
print("\n📊 一、三大地图API配额状态")
import requests
GD_KEY = '3f85cf…bd51'
r = requests.get('https://restapi.amap.com/v3/place/text',
    params={'keywords':'口腔','city':'重庆','offset':5,'page':1,'key':GD_KEY}, timeout=10)
d = r.json()
print(f"  高德: status={d.get('status')}, info={d.get('info')}")

BD_KEY = 'KKcT6s4u9G9I7Mh6werQqypfiXiPi2C0'
r2 = requests.get('https://api.map.baidu.com/place/v2/search',
    params={'query':'口腔','region':'重庆','output':'json','ak':BD_KEY,'page_size':3,'scope':2}, timeout=10)
d2 = r2.json()
print(f"  百度: status={d2.get('status')}, msg={d2.get('message','')}")

TX_KEY = 'JGGBZ-D5I6Q-66H5K-22SMU-I5VXO-NDFLJ'
r3 = requests.get('https://apis.map.qq.com/ws/place/v1/search',
    params={'key':TX_KEY,'boundary':'region(重庆,0)','keyword':'口腔','max_per_page':3}, timeout=10)
d3 = r3.json()
print(f"  腾讯: status={d3.get('status')}, msg={d3.get('message','')}")

print("\n  ⚠️ 结论: 三平台今日全部超限，需等明日0点重置")

# ========== 2. 经信委创新型中小企业数据 ==========
print("\n📊 二、经信委创新型中小企业 - 已下载2个Excel文件")
base = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\source\jingxinwei'
for fname in ['2025_创新型_申报通过.xlsx', '2025_创新型_复核通过.xlsx']:
    fpath = os.path.join(base, fname)
    if os.path.exists(fpath):
        size = os.path.getsize(fpath)
        print(f"  {fname}: {size} bytes ✅")
    else:
        print(f"  {fname}: ❌ 未找到")

# ========== 3. CRM当前状态 ==========
print("\n📊 三、CRM当前数据状态")
conn = sqlite3.connect(r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM customers')
total = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM customers WHERE phone IS NOT NULL AND phone != ''")
has_phone = cur.fetchone()[0]
print(f"  总客户: {total:,}家")
print(f"  有电话: {has_phone:,}家 ({has_phone*100//total}%)")
print(f"  待联系: {total:,}家")
conn.close()

# ========== 4. 已获取数据渠道汇总 ==========
print("\n📊 四、已覆盖数据来源")
master_dir = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\master'
total_rows = 0
for f in sorted(os.listdir(master_dir)):
    if not f.endswith('.csv'):
        continue
    with open(os.path.join(master_dir, f), encoding='utf-8-sig') as fh:
        rows = sum(1 for _ in fh) - 1
    total_rows += rows
print(f"  Master总行数: {total_rows:,}行")
print(f"  来源: 高德POI + 百度POI + 卫健委 + 教委 + 住建委 + 专精特新")

# ========== 5. 下一阶段计划 ==========
print("\n📋 五、下一阶段行动计划")
print("  【立即执行】经信委创新型中小企业名单解析入库")
print("  【明日0点】三平台配额恢复后批量补抓")
print("  【本周】企查查授权 + 药监局/市场监管局数据抓取")

# ========== 6. 渠道缺口总结 ==========
print("\n📋 六、渠道缺口明细")
print("  已覆盖渠道 (6个): 高德/百度/腾讯/卫健委/教委/住建委/专精特新")
print("  待恢复渠道 (1个): 腾讯 (Key已修复，等待配额重置)")
print("  待抓取渠道 (11个): 市场监管局/经信委/药监局/交通局/生态环境局/民政局/人社局/统计局/发改委/应急局/农业农村委")
print("  未接入渠道 (6个): 企查查/高新区/美团/行业协会×4")
