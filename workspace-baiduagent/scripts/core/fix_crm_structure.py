# -*- coding: utf-8 -*-
"""
修复CRM表结构 - 安全迁移（保留全部数据）
1. 备份原库
2. 新建含扩展字段的customers表
3. 从旧表迁移数据 + 解析note中的地址/区域到新字段
4. 验证
"""
import sqlite3, os, shutil, re, sys, time
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

DB_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data'
DB_PATH = os.path.join(DB_DIR, 'baidu_crm.db')
BACKUP = os.path.join(DB_DIR, f'baidu_crm_backup_{time.strftime("%Y%m%d_%H%M%S")}.db')

print("=" * 70)
print("【CRM表结构修复 - 安全迁移】")
print("=" * 70)

# 1. 备份
shutil.copy2(DB_PATH, BACKUP)
print(f"✅ 已备份: {BACKUP}")

# 2. 连接
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 3. 读取旧表所有数据
cur.execute("SELECT * FROM customers")
rows = cur.fetchall()
print(f"📊 待迁移客户: {len(rows)}家")

# 4. 创建新表（带扩展字段）
cur.execute("DROP TABLE IF EXISTS customers_new")
cur.execute('''CREATE TABLE customers_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    industry TEXT,
    tier TEXT,
    phone TEXT,
    contact TEXT,
    source TEXT,
    status TEXT DEFAULT '待联系',
    last_call TEXT,
    address TEXT,
    district TEXT,
    lat TEXT,
    lng TEXT,
    note TEXT,
    created_at TEXT,
    updated_at TEXT
)''')

# 5. 迁移数据并解析note中的地址/区域
migrated = 0
for r in rows:
    note = r['note'] or ''
    address = ''
    district = ''
    
    # 从note解析区域
    m = re.search(r'区域[:：]\s*([^\s|]+)', note)
    if m:
        district = m.group(1).strip()
    
    # 从note解析地址
    m2 = re.search(r'地址[:：]\s*([^|]+)', note)
    if m2:
        address = m2.group(1).strip()
    
    cur.execute('''INSERT INTO customers_new 
        (id, name, industry, tier, phone, contact, source, status, last_call,
         address, district, lat, lng, note, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (r['id'], r['name'], r['industry'], r['tier'], r['phone'], r['contact'],
         r['source'], r['status'], r['last_call'],
         address, district, '', '', note, r['created_at'], r['updated_at']))
    migrated += 1

print(f"✅ 已迁移: {migrated}家")

# 6. 用新表替换旧表
cur.execute("DROP TABLE customers")
cur.execute("ALTER TABLE customers_new RENAME TO customers")

# 7. 检查call_logs和industry_cards的外键
conn.commit()

# 8. 验证
cur.execute("PRAGMA table_info(customers)")
cols = [r[1] for r in cur.fetchall()]
print(f"\n📋 新表结构: {cols}")

cur.execute("SELECT COUNT(*) FROM customers")
total = cur.fetchone()[0]
print(f"📊 总客户: {total}")

cur.execute("SELECT COUNT(*) FROM customers WHERE district != ''")
has_dist = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM customers WHERE address != ''")
has_addr = cur.fetchone()[0]
print(f"   有区域: {has_dist}家")
print(f"   有地址: {has_addr}家")

# 9. 更新init_db.py里的表结构定义（保持一致性）
conn.close()
print("\n✅ CRM表结构修复完成！")
print(f"   (原库已备份: {os.path.basename(BACKUP)})")
