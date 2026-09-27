# -*- coding: utf-8 -*-
"""高德房产中介补抓 + 导入CRM（修复版）"""
import sys, os, time, csv, sqlite3, requests
sys.stdout.reconfigure(encoding='utf-8')

GD_KEY = '3f85cf676f4eb0ccb2374560bb99bd51'
BASE = 'https://restapi.amap.com/v3/place/text'
DB_PATH = 'data/baidu_crm.db'
MASTER_DIR = 'data/master'
districts = ['渝中','江北','南岸','九龙坡','沙坪坝','北碚','大渡口','巴南','高新','两江']

KEYWORDS = ['房产中介','房屋中介','房地产经纪','房产销售']

all_items = []
seen = set()

for kw in KEYWORDS:
    print(f'\n📂 关键词: {kw}')
    for page in range(1, 15):
        try:
            r = requests.get(BASE, params={
                'key': GD_KEY, 'keywords': kw,
                'city': '重庆', 'offset': 50, 'page': page, 'extensions': 'all'
            }, timeout=15).json()
            if r.get('status') != '1' or r.get('info') != 'OK':
                print(f'  p{page}: status={r.get("status")}, info={r.get("info")} - 停止')
                break
            pois = r.get('pois', [])
            if not pois:
                break
            new_count = 0
            for p in pois:
                name = p.get('name', '').strip()
                if not name or name in seen:
                    continue
                area = p.get('adname', '')
                if not any(d in area for d in districts):
                    continue
                tel = (p.get('tel') or '').replace(';', ',').replace('；', ',')
                loc = p.get('entr_location') or p.get('location', '')
                lng, lat = '', ''
                if loc:
                    parts = loc.split(',')
                    if len(parts) >= 2:
                        lng, lat = parts[0], parts[1]
                seen.add(name)
                all_items.append({
                    '区域': area, '机构名称': name, '地址': p.get('address', ''),
                    '电话': tel, '经度': lng, '纬度': lat
                })
                new_count += 1
            print(f'  p{page}: +{new_count} (累计{len(all_items)})')
            if new_count == 0:
                break
        except Exception as e:
            print(f'  p{page}: 异常 {e}')
            break

print(f'\n房产去重后: {len(all_items)}条, 有电话: {sum(1 for i in all_items if i["电话"])}家')

# 保存master
os.makedirs(MASTER_DIR, exist_ok=True)
out = os.path.join(MASTER_DIR, f'房产中介_gaode_{time.strftime("%Y%m%d")}.csv')
fieldnames = ['区域','机构名称','地址','电话','经度','纬度','数据来源','抓取时间']
with open(out, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for item in all_items:
        w.writerow({**item, '数据来源': '高德地图POI', '抓取时间': time.strftime('%Y-%m-%d %H:%M')})
print(f'已保存: {out}')

# 导入CRM - 用address字段
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
ins = skip = dup = 0
for row in all_items:
    name = row['机构名称'].strip()
    # 检查是否已存在
    c.execute('SELECT id FROM customers WHERE name = ?', (name,))
    existing = c.fetchone()
    if existing:
        dup += 1
        continue
    try:
        c.execute('''
            INSERT INTO customers(name, industry, phone, address, district, lat, lng, source, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
        ''', (
            name, '房产中介', row['电话'], row['地址'], row['区域'],
            row['纬度'], row['经度'], '高德POI-房产中介', '待联系'
        ))
        ins += c.rowcount
    except Exception as e:
        print(f'  导入错误 {name}: {e}')
        skip += 1

conn.commit()
conn.close()
has_phone = sum(1 for i in all_items if i['电话'])
print(f'✅ 导入CRM: +{ins}条, 已存在{dup}条, 错误{skip}条')
print(f'   有电话: {has_phone}家 ({round(has_phone/len(all_items)*100,1) if all_items else 0}%)')

# 验证
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute('SELECT COUNT(*) FROM customers')
total = c.fetchone()[0]
c.execute('SELECT COUNT(*) FROM customers WHERE phone IS NOT NULL AND phone != ""')
has_phone_total = c.fetchone()[0]
c.execute('SELECT COUNT(*) FROM customers WHERE industry = ?', ('房产中介',))
realty_count = c.fetchone()[0]
conn.close()
print(f'\nCRM总客户: {total:,}')
print(f'有电话: {has_phone_total:,} ({round(has_phone_total/total*100,1)}%)')
print(f'房产中介行业: {realty_count}家')
