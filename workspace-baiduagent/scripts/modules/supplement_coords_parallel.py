# -*- coding: utf-8 -*-
"""批量补充坐标 - 高并发版"""
import requests, sys, time, sqlite3, os, json
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.stdout.reconfigure(encoding='utf-8')

AK = 'KKcT6s4u9G9I7Mh6werQqypfiXiPi2C0'
DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
PROGRESS_FILE = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\coord_progress.json'

def geocode_row(args):
    cid, name, addr, dist = args
    search_addr = name if not addr else addr
    if dist and dist not in search_addr:
        search_addr = f"{search_addr} {dist}"
    try:
        r = requests.get('https://api.map.baidu.com/geocoding/v3/',
            params={'ak': AK, 'address': search_addr, 'output': 'json'}, timeout=10)
        d = r.json()
        if d.get('status') == 0 and d.get('result'):
            loc = d['result'].get('location', {})
            lat, lng = loc.get('lat'), loc.get('lng')
            if lat and lng:
                return (cid, lat, lng, True)
    except:
        pass
    return (cid, None, None, False)

print("=" * 70)
print("【批量补充坐标 - 高并发版】")
print("=" * 70)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 查询所有无坐标客户
cur.execute("SELECT id, name, address, district FROM customers WHERE lat IS NULL OR lat = ''")
all_rows = cur.fetchall()
total = len(all_rows)

# 读取进度
progress = {'done': 0, 'success': 0}
if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, encoding='utf-8') as f:
        progress = json.load(f)

start_idx = progress.get('done', 0)
remaining = total - start_idx
print(f"待补充: {total}家，已完成: {start_idx}家，剩余: {remaining}家")

# 高并发处理（10线程）
success_count = 0
batch_size = 50
threads = 10

for batch_start in range(start_idx, total, batch_size):
    batch_end = min(batch_start + batch_size, total)
    batch = all_rows[batch_start:batch_end]
    
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(geocode_row, row): row for row in batch}
        for future in as_completed(futures):
            cid, lat, lng, ok = future.result()
            if ok and lat and lng:
                cur.execute("UPDATE customers SET lat=?, lng=? WHERE id=?", (lat, lng, cid))
                success_count += 1
    
    # 每批提交
    conn.commit()
    progress['done'] = batch_end
    progress['success'] = progress.get('success', 0) + success_count
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False)
    
    print(f"  批次 {batch_end}/{total}，成功: {success_count}")
    time.sleep(0.5)

conn.close()

# 最终统计
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM customers WHERE lat IS NOT NULL AND lat != ''")
has_coord = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM customers")
total_cust = cur.fetchone()[0]

print(f"\n✅ 完成！有坐标: {has_coord}/{total_cust} ({has_coord*100//total_cust}%)")
conn.close()
