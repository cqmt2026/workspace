import sqlite3
import os

DB_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, 'baidu_crm.db')

# 强制删除旧文件重建
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print(f"[DEL] 已删除旧数据库: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# 客户表
c.execute('''CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    industry TEXT,
    tier TEXT CHECK(tier IN ('A','B','C')),
    phone TEXT,
    contact TEXT,
    source TEXT,
    status TEXT CHECK(status IN ('待联系','已联系','有意向','已成交','放弃')) DEFAULT '待联系',
    last_call TEXT,
    address TEXT,
    district TEXT,
    lat TEXT,
    lng TEXT,
    note TEXT,
    created_at TEXT DEFAULT (datetime('now','localtime')),
    updated_at TEXT DEFAULT (datetime('now','localtime'))
)''')

# 通话记录表
c.execute('''CREATE TABLE call_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    call_date TEXT DEFAULT (date('now','localtime')),
    duration_sec INTEGER,
    result TEXT CHECK(result IN ('有效','无效','关机','拒接','有意向','需跟进')),
    next_action TEXT,
    script_version TEXT,
    note TEXT,
    FOREIGN KEY(customer_id) REFERENCES customers(id)
)''')

# 行业数据卡表
c.execute('''CREATE TABLE industry_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    industry TEXT UNIQUE,
    search_volume TEXT,
    competitor_count TEXT,
    avg_cpc TEXT,
    key_words TEXT,
    tip TEXT,
    updated_at TEXT DEFAULT (datetime('now','localtime'))
)''')

conn.commit()
conn.close()
print(f"[OK] 数据库已创建: {DB_PATH}")

# 验证
conn2 = sqlite3.connect(DB_PATH)
cur2 = conn2.cursor()
cur2.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur2.fetchall()]
print(f"[OK] 表结构: {tables}")
conn2.close()
