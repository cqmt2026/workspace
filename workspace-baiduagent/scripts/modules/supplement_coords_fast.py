# -*- coding: utf-8 -*-
"""批量补充坐标 - 快速串行版"""
import requests, sys, time, sqlite3, os, json
sys.stdout.reconfigure(encoding='utf-8')

AK = 'KKcT6s4u9G9I7Mh6werQqypfiXiPi2C0'
DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
PROGRESS_FILE = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\coord_progress.json'

print("=" * 70)
print("【批量补充坐标 - 快速执行】")
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

success_count = 0
interval = 0.05  # 极短间隔
last_commit = 0
commit_interval = 100  # 每100条提交一次

for i in range(start_idx, total):
    row = all_rows[i]
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
                success_count += 1
    except:
        pass
    
    time.sleep(interval)
    
    # 定期提交
    if (i + 1 - last_commit) >= commit_interval:
        conn.commit()
        last_commit = i + 1
        progress['done'] = i + 1
        progress['success'] = success_count
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False)
        pct = (i + 1) * 100 // total
        print(f"  进度: {i+1}/{total} ({pct}%)，成功: {success_count}")

conn.commit()
progress['done'] = total
progress['success'] = success_count
with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
    json.dump(progress, f, ensure_ascii=False)

# 最终统计
cur.execute("SELECT COUNT(*) FROM customers WHERE lat IS NOT NULL AND lat != ''")
has_coord = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM customers")
total_cust = cur.fetchone()[0]

print(f"\n✅ 完成！有坐标: {has_coord}/{total_cust} ({has_coord*100//total_cust}%)")
print(f"   本次新增: {success_count}条")
conn.close()
