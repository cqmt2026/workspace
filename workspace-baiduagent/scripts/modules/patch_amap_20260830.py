#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""高德POI补抓低覆盖率行业 - 使用正确的Key"""
import sys, os, time, csv, sqlite3, requests
sys.stdout.reconfigure(encoding='utf-8')

# 高德Key（正确）
AMAP_KEY = '3f85cf676f4eb0ccb2374560bb99bd51'
BASE_URL = 'https://restapi.amap.com/v3/place/text'
DB_PATH = 'data/baidu_crm.db'
MASTER_DIR = 'data/master'

# 重庆主城区9区
CITY_CODES = {
    '渝中区': '500103', '江北区': '500105', '南岸区': '500108',
    '九龙坡区': '500107', '沙坪坝区': '500106', '北碚区': '500109',
    '大渡口区': '500104', '巴南区': '500113', '高新区': '500372',
}

# 低覆盖率行业配置
INDUSTRIES = [
    {'name': '人力资源', 'keywords': ['人力资源公司','劳务派遣','猎头公司','人才市场','人事代理'], 'target': 300},
    {'name': '检验检测', 'keywords': ['检测公司','质检机构','质量检测','环境检测','第三方检测'], 'target': 200},
    {'name': '物流货运', 'keywords': ['物流公司','货运公司','物流园','仓储物流','运输公司'], 'target': 300},
    {'name': '软件信息', 'keywords': ['软件公司','软件开发','IT服务','信息系统','网络科技'], 'target': 200},
    {'name': '智能制造', 'keywords': ['智能装备','工业机器人','自动化设备','智能科技'], 'target': 150},
    {'name': '能源环保补充', 'keywords': ['环保公司','环保科技','环境工程','水处理','废气处理'], 'target': 150},
    {'name': '食品加工', 'keywords': ['食品公司','食品加工','食品科技','饮料制造','糕点制造'], 'target': 150},
    {'name': '电子科技', 'keywords': ['电子科技','电子产品','电子元器件','电子器件'], 'target': 100},
]

def fetch_industry(industry_cfg):
    name = industry_cfg['name']
    keywords = industry_cfg['keywords']
    target = industry_cfg['target']
    
    print(f"\n{'='*60}")
    print(f"抓取: {name} (目标>={target}条)")
    print(f"{'='*60}")
    
    all_items = []
    seen = set()
    quota_hit = False
    
    for kw in keywords:
        if quota_hit or len(all_items) >= target:
            break
        
        print(f"  关键词: {kw}")
        page = 1
        while True:
            params = {'key': AMAP_KEY, 'keywords': kw, 'city': '重庆', 
                     'citylimit': 'true', 'offset': 20, 'page': page, 'output': 'JSON'}
            try:
                r = requests.get(BASE_URL, params=params, timeout=15)
                d = r.json()
                
                if d.get('status') != '1':
                    info = d.get('info', '')
                    print(f"    错误: {info}")
                    if 'limit' in info.lower() or 'over' in info.lower():
                        quota_hit = True
                    break
                
                pois = d.get('pois', [])
                if not pois:
                    break
                
                new_count = 0
                for poi in pois:
                    title = poi.get('name', '').strip()
                    if not title or title in seen:
                        continue
                    
                    addr = poi.get('address', '')
                    area = '高新区'
                    for dist in CITY_CODES.keys():
                        if dist in addr:
                            area = dist
                            break
                    
                    seen.add(title)
                    tel = poi.get('tel', '')
                    if tel:
                        tel = ''.join(c for c in tel if c.isdigit())
                        if len(tel) < 7:
                            tel = ''
                    
                    loc = poi.get('location', '').split(',')
                    all_items.append({
                        '区域': area, '机构名称': title, '地址': addr,
                        '电话': tel, '机构类别': name,
                        '经度': loc[0] if len(loc)>0 else '',
                        '纬度': loc[1] if len(loc)>1 else '',
                        '数据来源': '高德POI', '抓取时间': time.strftime('%Y-%m-%d %H:%M'),
                    })
                    new_count += 1
                
                print(f"    第{page}页: +{new_count}条 (累计{len(all_items)}条)")
                time.sleep(0.1)
                page += 1
                
                if new_count == 0:
                    break
                    
            except Exception as e:
                print(f"    异常: {e}")
                break
    
    print(f"\n[{name}] 完成: {len(all_items)}条, 有电话{sum(1 for i in all_items if i['电话'])}条")
    return all_items, quota_hit

def import_to_crm(items, source_tag):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    inserted = skipped = 0
    for row in items:
        cur.execute("SELECT id FROM customers WHERE name = ?", (row['机构名称'],))
        if cur.fetchone():
            skipped += 1
            continue
        cur.execute("""INSERT INTO customers 
            (name, industry, phone, address, district, lat, lng, source, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))""",
            (row['机构名称'], row['机构类别'], row['电话'], row['地址'], row['区域'],
             row['纬度'], row['经度'], source_tag, '待联系'))
        inserted += cur.rowcount
    conn.commit()
    conn.close()
    return inserted, skipped

def main():
    print("="*60)
    print("【高德POI补抓低覆盖率行业】")
    print("="*60)
    
    all_inserted = all_skipped = 0
    quota_limited = False
    
    for cfg in INDUSTRIES:
        if quota_limited:
            print("\n⚠️ 配额受限，停止")
            break
        
        items, quota_limited = fetch_industry(cfg)
        if not items:
            continue
        
        # 保存
        out_path = os.path.join(MASTER_DIR, f"{cfg['name']}_amap_20260830.csv")
        with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['区域','机构名称','地址','电话','机构类别','经度','纬度','数据来源','抓取时间'])
            writer.writeheader()
            writer.writerows(items)
        
        # 导入CRM
        ins, skip = import_to_crm(items, f"高德POI补抓-{cfg['name']}")
        all_inserted += ins
        all_skipped += skip
        
        phones = sum(1 for i in items if i['电话'])
        print(f"  导入CRM: +{ins}条(电话{phones}), 跳过{skip}")
        time.sleep(0.5)
    
    # 验证
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM customers')
    total = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM customers WHERE phone IS NOT NULL AND phone != ""')
    has_phone = cur.fetchone()[0]
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"【完成】新增{all_inserted}条, CRM总计{total:,}, 有电话{has_phone:,}({round(has_phone/total*100,1)}%)")

if __name__ == '__main__':
    main()
