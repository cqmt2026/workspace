import sqlite3, requests, time, json
from datetime import datetime

db = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
BAIDU_AK = 'KKcT6s4u9G9I7Mh6werQqypfiXiPi2C0'

conn = sqlite3.connect(db)
c = conn.cursor()

print("=" * 60)
print("【创新型中小企业 - 百度POI批量补抓】")
print("=" * 60)

# 区县列表
districts = ['万州区', '涪陵区', '渝中区', '大渡口区', '江北区', '沙坪坝区', 
             '九龙坡区', '南岸区', '北碚区', '渝北区', '巴南区', '高新区']

keywords = ['科技有限公司', '机械有限公司', '工贸有限公司', '实业有限公司', 
            '建材有限公司', '新能源科技', '生物科技', '电子科技']

updated = 0
searched = 0
quota_hit = False

for district in districts:
    if quota_hit:
        break
    
    print(f"\n【{district}】")
    
    for kw in keywords:
        if quota_hit:
            break
        
        for page in range(3):
            if quota_hit:
                break
            
            url = 'https://api.map.baidu.com/place/v2/search'
            params = {
                'query': f'{kw}',
                'region': district,
                'output': 'json',
                'ak': BAIDU_AK,
                'page_size': 20,
                'page_num': page,
                'scope': 2,
            }
            
            try:
                r = requests.get(url, params=params, timeout=10)
                data = r.json()
                
                if data.get('status') != 0:
                    info = data.get('info', 'error')
                    if 'LIMIT' in info.upper() or 'QUOTA' in info.upper():
                        quota_hit = True
                        print(f"  配额耗尽!")
                    break
                
                results = data.get('results', [])
                if not results:
                    break
                
                searched += len(results)
                
                for item in results:
                    name = item.get('name', '').strip()
                    tel = item.get('tel', '') or item.get('telephone', '') or ''
                    addr = item.get('address', '')
                    
                    # 检查是否创新型中小企业且无电话
                    c.execute("""
                        SELECT id FROM customers 
                        WHERE name = ? AND industry LIKE '%创新型%'
                        AND (phone IS NULL OR phone = '' OR phone = '无')
                    """, (name,))
                    
                    row = c.fetchone()
                    if row and tel:
                        c.execute("""
                            UPDATE customers 
                            SET phone = ?, address = COALESCE(address, ?),
                                source = source || '+百度POI',
                                updated_at = ?
                            WHERE id = ?
                        """, (tel, addr, datetime.now().strftime('%Y-%m-%d %H:%M'), row[0]))
                        
                        if c.rowcount > 0:
                            updated += 1
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  错误: {e}")
                break
    
    print(f"  已更新{updated}条")

conn.commit()
conn.close()

print(f"\n{'='*60}")
print(f"完成!")
print(f"  搜索: {searched}条")
print(f"  更新电话: {updated}条")

# 最终统计
conn = sqlite3.connect(db)
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM customers WHERE industry LIKE '%创新型%'")
total = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM customers WHERE industry LIKE '%创新型%' AND phone IS NOT NULL AND phone != ''")
has_phone = c.fetchone()[0]
print(f"  创新型总数: {total}家")
print(f"  有电话: {has_phone}家 ({has_phone*100//total if total>0 else 0}%)")
conn.close()