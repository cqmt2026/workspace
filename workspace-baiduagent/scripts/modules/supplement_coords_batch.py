# -*- coding: utf-8 -*-
"""批量补充坐标 - 分段执行版"""
import requests, sys, time, sqlite3, os, json
sys.stdout.reconfigure(encoding='utf-8')

AK = 'KKcT6s4u9G9I7Mh6werQqypfiXiPi2C0'
DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
PROGRESS_FILE = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\coord_progress.json'

# 读取进度
progress = {'done': 200}
if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, encoding='utf-8') as f:
        progress = json.load(f)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 查询所有无坐标客户
cur.execute("SELECT id, name, address, district FROM customers WHERE lat IS NULL OR lat = ''")
all_rows = cur.fetchall()
total = len(all_rows)
start = progress.get('done', 0)
remaining = total - start

print(f"总待补充: {total}家，已完成: {start}家，剩余: {remaining}家")

# 分批处理
BATCH = 100  # 每批数量
for batch_start in range(start, total, BATCH):
    batch_end = min(batch_start + BATCH, total)
    batch = all_rows[batch_start:batch_end]
    
    for row in batch:
        cid, name, addr, dist = row
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
                    cur.execute("UPDATE customers SET lat=?, lng=? WHERE id=?", (lat, lng, cid))
        except:
            pass
        time.sleep(0.1)
    
    conn.commit()
    progress['done'] = batch_end
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False)
    
    print(f"  已处理 {batch_end}/{total} ({batch_end*100//total}%)")
    time.sleep(0.5)

# 最终统计
cur.execute("SELECT COUNT(*) FROM customers WHERE lat IS NOT NULL AND lat != ''")
has_coord = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM customers")
total_cust = cur.fetchone()[0]

print(f"\n✅ 完成！有坐标: {has_coord}/{total_cust} ({has_coord*100//total_cust}%)")
conn.close()
