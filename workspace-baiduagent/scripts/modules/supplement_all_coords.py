# -*- coding: utf-8 -*-
"""
批量补充所有客户坐标 - 分页续跑版
百度geocoding独立配额，支持断点续跑
"""
import requests, sys, time, sqlite3, os, json
sys.stdout.reconfigure(encoding='utf-8')

AK = 'KKcT6s4u9G9I7Mh6werQqypfiXiPi2C0'
DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
PROGRESS_FILE = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\coord_progress.json'

# 读取进度
progress = {}
if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, encoding='utf-8') as f:
        progress = json.load(f)

# 每批处理数（避免单次运行过长）
BATCH_SIZE = 500

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 查询所有无坐标客户
cur.execute("SELECT id, name, address, district FROM customers WHERE lat IS NULL OR lat = ''")
all_rows = cur.fetchall()
total_pending = len(all_rows)
print(f"待补充坐标: {total_pending}家")

# 从断点继续
start = progress.get('done', 0)
if start > 0:
    print(f"已处理: {start}家，继续...")
    all_rows = all_rows[start:]

success = 0
fail = 0
rate_limited = 0
processed = 0

for row in all_rows:
    cid, name, addr, dist = row
    search_addr = name if not addr else addr
    if dist and dist not in search_addr:
        search_addr = f"{search_addr} {dist}"
    
    try:
        r = requests.get('https://api.map.baidu.com/geocoding/v3/',
            params={'ak': AK, 'address': search_addr, 'output': 'json'}, timeout=10)
        d = r.json()
        st = d.get('status')
        if st == 0 and d.get('result'):
            loc = d['result'].get('location', {})
            lat, lng = loc.get('lat'), loc.get('lng')
            if lat and lng:
                cur.execute("UPDATE customers SET lat=?, lng=? WHERE id=?", (lat, lng, cid))
                success += 1
        elif st == 302 or st == 401:
            # 配额超限或未认证，停止
            rate_limited += 1
            print(f"⚠️ 触发限流(status={st})，停止本次批处理")
            break
        else:
            fail += 1
        processed += 1
        # 每100条提交+保存进度
        if processed % 100 == 0:
            conn.commit()
            progress['done'] = start + processed
            with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
                json.dump(progress, f, ensure_ascii=False)
            print(f"  已处理 {start+processed}/{total_pending+start}，成功{success}，失败{fail}")
        time.sleep(0.15)  # 控制频率
    except Exception as e:
        fail += 1
        processed += 1

conn.commit()
progress['done'] = start + processed
with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
    json.dump(progress, f, ensure_ascii=False)

# 最终统计
cur.execute("SELECT COUNT(*) FROM customers WHERE lat IS NOT NULL AND lat != ''")
has_coord = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM customers")
total = cur.fetchone()[0]

print(f"\n📊 本批结果:")
print(f"   成功: {success}")
print(f"   失败: {fail}")
print(f"   限流: {rate_limited}")
print(f"   累计有坐标: {has_coord}/{total} ({has_coord*100//total}%)")
conn.close()
