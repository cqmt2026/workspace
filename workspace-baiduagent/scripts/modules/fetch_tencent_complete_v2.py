# -*- coding: utf-8 -*-
"""
腾讯地图POI批量抓取 - 基于官方文档修正版
一个行业彻底完成再继续下一个（方法论修正版）
关键修正：boundary参数格式、分页逻辑、最大200条限制
"""
import requests, sys, time, csv, os, sqlite3
sys.stdout.reconfigure(encoding='utf-8')

# 从环境变量读取Key
TX_KEY = ***'TX_MAP_KEY', '')
if not TX_KEY:
    ***'❌ 未配置TX_MAP_KEY环境变量')
    print('请执行: set TX_MAP_KEY=***')
    sys.exit(1)

BASE = 'https://apis.map.qq.com/ws/place/v1/search'
OUT_DIR = r'data\source\tencent'
MASTER_DIR = r'data\master'
DB_PATH = r'data\baidu_crm.db'
os.makedirs(OUT_DIR, exist_ok=True)

districts = ['渝中区','江北区','南岸区','九龙坡区','沙坪坝区',
             '北碚区','大渡口区','巴南区','高新区','两江新区']

# 目标行业 - 按业务价值排序
TARGETS = [
    {'name': '人力资源', 'keywords': ['人力资源公司','劳务派遣','猎头公司','人才市场','企业管理咨询'], 'threshold': 300},
    {'name': '软件信息', 'keywords': ['软件公司','软件开发','软件研发','IT服务','信息系统'], 'threshold': 200},
    {'name': '物流货运', 'keywords': ['物流公司','货运公司','物流园','仓储物流','快递公司'], 'threshold': 300},
    {'name': '智能制造', 'keywords': ['智能制造','智能装备','工业机器人','自动化设备'], 'threshold': 150},
    {'name': '检验检测', 'keywords': ['检测公司','质检','质量检测','检测机构'], 'threshold': 200},
]

def fetch_all_pages(keyword):
    """按照官方文档正确调用"""
    all_results = []
    seen_names = set()
    quota_hit = False
    
    for page in range(1, 26):  # 最多25页，每页20条 = 500条，但官方说最多200条
        params = {
            'key': TX_KEY,
            'boundary': 'region(重庆,0)',
            'keyword': keyword,
            'max_per_page': 20,
            'page': page,
        }
        try:
            r = requests.get(BASE, params=params, timeout=10)
            d = r.json()
            
            if d.get('status') != 0:
                msg = d.get('message', '')
                print(f"    ❌ 错误: {msg}")
                if '配额' in msg or '超限' in msg:
                    quota_hit = True
                break
            
            data = d.get('data', [])
            count = d.get('count', 0)
            print(f"    第{page}页: +{len(data)}条 (本类总计{count}条, 累计{len(all_results)}条)")
            
            if not data:
                break
            
            new_count = 0
            for item in data:
                name = item.get('title', '').strip()
                if not name or name in seen_names:
                    continue
                
                ad_info = item.get('ad_info', {})
                area = ad_info.get('district', '')
                if area and not any(d in area for d in districts):
                    continue
                
                seen_names.add(name)
                loc = item.get('location', {})
                all_results.append({
                    '区域': area,
                    '机构名称': name,
                    '地址': item.get('address', ''),
                    '电话': item.get('tel', ''),
                    '机构类别': '',
                    '经度': loc.get('lng', ''),
                    '纬度': loc.get('lat', ''),
                    '数据来源': '腾讯地图POI',
                    '抓取时间': time.strftime('%Y-%m-%d %H:%M'),
                    '分类': item.get('category', ''),
                })
                new_count += 1
            
            time.sleep(0.1)
            
            # 达到上限或无新数据则停止
            if new_count == 0:
                break
            if len(all_results) >= 200:  # 官方限制最多200条
                print(f"    ⚠️ 已达官方上限(200条)")
                break
                
        except Exception as e:
            print(f"    ❌ 异常: {e}")
            time.sleep(1)
    
    return all_results, quota_hit

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
            row['机构名称'], row['机构类别'], row['电话'], row['地址'], row['区域'],
            row['纬度'], row['经度'], source_tag, '待联系'
        ))
        inserted += cur.rowcount
    conn.commit()
    conn.close()
    return inserted, skipped

def main():
    print("="*70)
    print("【腾讯地图POI批量抓取 - 官方文档修正版】")
    print(f"Key: {TX_KEY[:4]}...{TX_KEY[-4:]} (长度:{len(TX_KEY)})")
    print("="*70)
    
    all_inserted = all_skipped = 0
    quota_hit = False
    
    for idx, cfg in enumerate(TARGETS, 1):
        if quota_hit:
            print(f"\n⚠️ 配额已耗尽，停止后续行业")
            break
        
        print(f"\n▶ 第{idx}/{len(TARGETS)}个行业: {cfg['name']}")
        print("-"*60)
        
        industry_items = []
        for kw in cfg['keywords']:
            if quota_hit:
                break
            items, quota_hit = fetch_all_pages(kw)
            for item in items:
                item['机构类别'] = cfg['name']
            industry_items.extend(items)
        
        if not industry_items:
            print(f"[{cfg['name']}] 无新数据")
            continue
        
        # 保存
        out_path = os.path.join(MASTER_DIR, f"{cfg['name']}_tencent_v2.csv")
        fieldnames = ['区域','机构名称','地址','电话','机构类别','经度','纬度','数据来源','抓取时间','分类']
        with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(industry_items)
        
        # 导入CRM
        inserted, skipped = import_to_crm(industry_items, f"腾讯POIv2-{cfg['name']}")
        all_inserted += inserted
        all_skipped += skipped
        
        phone_count = sum(1 for i in industry_items if i['电话'])
        print(f"[{cfg['name']}] 完成: {len(industry_items)}条, 电话{phone_count}条, CRM+{inserted}条")
        
        time.sleep(0.5)
    
    print(f"\n{'='*70}")
    print(f"【完成汇总】新增入库: {all_inserted}条, 跳过重复: {all_skipped}条")
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM customers')
    total = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM customers WHERE phone IS NOT NULL AND phone != ""')
    has_phone = cur.fetchone()[0]
    conn.close()
    
    print(f"CRM总客户: {total:,}, 有电话: {has_phone:,} ({round(has_phone/total*100,1)}%)")
    print(f"配额状态: {'已耗尽' if quota_hit else '正常'}")

if __name__ == '__main__':
    main()