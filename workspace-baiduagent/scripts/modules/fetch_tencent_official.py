# -*- coding: utf-8 -*-
"""
腾讯地图POI批量抓取 - 基于官方文档的正确实现
一个行业彻底完成再继续下一个（方法论修正版）

官方文档: https://lbs.qq.com/webservice_v1/guide-search.html
关键参数:
  - boundary=region(城市名)  # 区域搜索，不带,0
  - boundary=nearby(lat,lng,radius)  # 周边搜索，radius最大1000米
  - page_size=20, page_index=1  # 分页，每页最多20条
  - 单次最多返回200条
"""
import requests, sys, time, csv, os, sqlite3
sys.stdout.reconfigure(encoding='utf-8')

# 从环境变量读取Key（安全做法）
TX_KEY = '***'  # JGGBZ-D5I6Q-66H5K-22SMU-I5VXO-NDFLJ
if not TX_KEY or len(TX_KEY) < 30:
    ***('❌ Key无效，请检查')
    sys.exit(1)

BASE = 'https://apis.map.qq.com/ws/place/v1/search'
OUT_DIR = r'data\source\tencent'
MASTER_DIR = r'data\master'
DB_PATH = r'data\baidu_crm.db'
os.makedirs(OUT_DIR, exist_ok=True)

# 主城区9区过滤
districts = ['渝中区','江北区','南岸区','九龙坡区','沙坪坝区',
             '北碚区','大渡口区','巴南区','高新区','两江新区']

# 目标行业（按业务价值排序）
TARGETS = [
    {'name': '人力资源', 'keywords': ['人力资源公司','劳务派遣','猎头公司','人才市场','企业管理咨询','人事代理'], 'threshold': 300},
    {'name': '软件信息', 'keywords': ['软件公司','软件开发','软件研发','IT服务','信息系统','网络科技','信息技术'], 'threshold': 200},
    {'name': '物流货运', 'keywords': ['物流公司','货运公司','物流园','仓储物流','快递公司','货运代理'], 'threshold': 300},
    {'name': '检验检测', 'keywords': ['检测公司','质检','质量检测','检测机构','环境检测','食品检测'], 'threshold': 200},
    {'name': '智能制造', 'keywords': ['智能制造','智能装备','工业机器人','自动化设备','智能工厂'], 'threshold': 150},
]

def fetch_industry(industry_name, keywords, max_results=300):
    """彻底抓取一个行业的所有数据"""
    all_items = []
    seen_names = set()
    quota_hit = False
    
    print(f"\n{'='*60}")
    print(f"行业: {industry_name}")
    print(f"{'='*60}")
    
    for kw in keywords:
        if quota_hit:
            break
        
        print(f"\n  关键词: {kw}")
        page = 1
        while page <= 15:  # 最多15页（15*20=300条）
            params = {
                'key': TX_KEY,
                'boundary': 'region(重庆)',  # 官方格式
                'keyword': kw,
                'page_size': 20,
                'page_index': page
            }
            
            try:
                r = requests.get(BASE, params=params, timeout=15)
                d = r.json()
                
                if d.get('status') != 0:
                    msg = d.get('message', '')
                    print(f"    ❌ 错误: {msg}")
                    if '配额' in msg or '上限' in msg:
                        quota_hit = True
                    break
                
                data = d.get('data', [])
                count = d.get('count', 0)
                
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
                    all_items.append({
                        '区域': area,
                        '机构名称': name,
                        '地址': item.get('address', ''),
                        '电话': item.get('tel', ''),
                        '机构类别': industry_name,
                        '经度': loc.get('lng', ''),
                        '纬度': loc.get('lat', ''),
                        '数据来源': '腾讯地图POI',
                        '抓取时间': time.strftime('%Y-%m-%d %H:%M'),
                        '分类': item.get('category', ''),
                    })
                    new_count += 1
                
                print(f"    第{page}页: +{new_count}条 (累计{len(all_items)}条, 总数{count}条)")
                time.sleep(0.1)  # 腾讯限频较严
                
                if new_count == 0:
                    break
                if len(all_items) >= max_results:
                    print(f"    ⚠️ 已达目标({max_results}条)")
                    break
                page += 1
                
            except Exception as e:
                print(f"    ❌ 异常: {e}")
                time.sleep(1)
    
    phone_count = sum(1 for i in all_items if i['电话'])
    print(f"\n[{industry_name}] 完成: {len(all_items)}条, 电话{phone_count}条")
    return all_items, quota_hit

def import_to_crm(items, source_tag):
    """导入到CRM"""
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
        items, quota_hit = fetch_industry(cfg['name'], cfg['keywords'], cfg['threshold'])
        
        if not items:
            continue
        
        # 保存master文件
        out_path = os.path.join(MASTER_DIR, f"{cfg['name']}_tencent_official.csv")
        fieldnames = ['区域','机构名称','地址','电话','机构类别','经度','纬度','数据来源','抓取时间','分类']
        with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(items)
        
        # 导入CRM
        inserted, skipped = import_to_crm(items, f"腾讯POI官方-{cfg['name']}")
        all_inserted += inserted
        all_skipped += skipped
        
        phone_count = sum(1 for i in items if i['电话'])
        print(f"  CRM入库: +{inserted}条, 跳过{skipped}条")
        
        time.sleep(0.5)
    
    print(f"\n{'='*70}")
    print(f"【完成汇总】")
    print(f"新增入库: {all_inserted}条")
    print(f"跳过重复: {all_skipped}条")
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM customers')
    total = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM customers WHERE phone IS NOT NULL AND phone != ""')
    has_phone = cur.fetchone()[0]
    conn.close()
    
    print(f"CRM总客户: {total:,}")
    print(f"有电话: {has_phone:,} ({round(has_phone/total*100,1)}%)")
    print(f"配额状态: {'已耗尽' if quota_hit else '正常'}")
    if quota_hit:
        print("明日0点后可继续")

if __name__ == '__main__':
    main()