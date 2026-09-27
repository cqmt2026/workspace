# -*- coding: utf-8 -*-
"""房产物业高德补抓 + 导入CRM"""
import sys, os, time, csv, sqlite3, requests
sys.stdout.reconfigure(encoding='utf-8')

GD_KEY = '3f85cf676f4eb0ccb2374560bb99bd51'
BASE = 'https://restapi.amap.com/v3/place/text'
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'baidu_crm.db')

districts = ['渝中','江北','南岸','九龙坡','沙坪坝','北碚','大渡口','巴南','高新','两江']

INDUSTRY_CONFIGS = [
    {'name': '房产中介', 'keywords': ['房产中介','房屋中介','房地产经纪','房产销售'], 'tag': '高德POI-房产中介'},
    {'name': '物业服务', 'keywords': ['物业服务','物业公司','物业管理'], 'tag': '高德POI-物业服务'},
]

def fetch_all(kw):
    all_items = []
    seen = set()
    page = 1
    while True:
        try:
            r = requests.get(BASE, params={
                'key': GD_KEY, 'keywords': kw,
                'city': '重庆', 'offset': 50, 'page': page,
                'extensions': 'all'
            }, timeout=15)
            d = r.json()
            if d.get('status') != '1' or d.get('info') != 'OK':
                print(f'  {kw} p{page}: status={d.get("status")}, info={d.get("info")} - 停止')
                break
            pois = d.get('pois', [])
            if not pois:
                break
            new_count = 0
            for p in pois:
                name = p.get('name', '').strip()
                if not name or name in seen:
                    continue
                area = p.get('adname', '') or p.get('area', '')
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
                    '区域': area,
                    '机构名称': name,
                    '地址': p.get('address', ''),
                    '电话': tel,
                    '机构类别': '',
                    '经度': lng,
                    '纬度': lat,
                    '数据来源': '高德地图POI',
                    '抓取时间': time.strftime('%Y-%m-%d %H:%M'),
                })
                new_count += 1
            print(f'  {kw} p{page}: +{new_count} (累计{len(all_items)})')
            time.sleep(0.2)
            if new_count == 0:
                break
            page += 1
            if len(all_items) >= 500:
                print(f'  {kw} 已达到500条上限，停止')
                break
        except Exception as e:
            print(f'  {kw} p{page}: 异常 {e}')
            break
    return all_items

def import_to_crm(items, source_tag):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    inserted = skipped = 0
    for row in items:
        name = row['机构名称'].strip()
        cur.execute("SELECT id FROM customers WHERE name = ?", (name,))
        if cur.fetchone():
            skipped += 1
            continue
        cur.execute("""
            INSERT INTO customers (name, industry, phone, address, district, lat, lng, source, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
        """, (
            name, row['机构类别'], row['电话'], row['地址'], row['区域'],
            row['纬度'], row['经度'], source_tag, '待联系'
        ))
        inserted += cur.rowcount
    conn.commit()
    conn.close()
    return inserted, skipped

def main():
    print('=' * 60)
    print('【房产物业高德补抓】')
    print('=' * 60)
    
    total_inserted = total_skipped = 0
    
    for cfg in INDUSTRY_CONFIGS:
        print(f'\n📂 行业: {cfg["name"]}')
        all_items = []
        for kw in cfg['keywords']:
            items = fetch_all(kw)
            print(f'  => {kw}: {len(items)}条')
            all_items.extend(items)
        
        # 去重
        seen = set()
        unique_items = []
        for item in all_items:
            if item['机构名称'] not in seen:
                seen.add(item['机构名称'])
                unique_items.append(item)
        
        print(f'  去重后: {len(unique_items)}条')
        has_phone = sum(1 for i in unique_items if i['电话'])
        print(f'  有电话: {has_phone}家 ({round(has_phone/len(unique_items)*100,1) if unique_items else 0}%)')
        
        # 保存master
        master_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'master')
        os.makedirs(master_dir, exist_ok=True)
        out_path = os.path.join(master_dir, f'{cfg["name"]}_gaode_{time.strftime("%Y%m%d")}.csv')
        fieldnames = ['区域','机构名称','地址','电话','机构类别','经度','纬度','数据来源','抓取时间']
        with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(unique_items)
        print(f'  已保存: {out_path}')
        
        # 导入CRM
        inserted, skipped = import_to_crm(unique_items, cfg['tag'])
        total_inserted += inserted
        total_skipped += skipped
        print(f'  导入CRM: +{inserted}条, 跳过{skipped}条')
    
    # 验证
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM customers')
    total = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM customers WHERE phone IS NOT NULL AND phone != ""')
    has_phone = cur.fetchone()[0]
    conn.close()
    
    print(f'\n{"=" * 60}')
    print(f'【补抓完成】')
    print(f'本次入库: +{total_inserted}条')
    print(f'CRM总客户: {total:,}')
    print(f'有电话: {has_phone:,} ({round(has_phone/total*100,1)}%)')

if __name__ == '__main__':
    main()
