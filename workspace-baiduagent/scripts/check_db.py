import sqlite3, json, sys
from datetime import datetime

conn = sqlite3.connect('data/baidu_crm.db')
cur = conn.cursor()

# Check tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cur.fetchall()]
print('Tables:', tables)

# Check schema and sample data
for tname in tables:
    cur.execute(f"PRAGMA table_info({tname})")
    cols = cur.fetchall()
    col_names = [c[1] for c in cols]
    cur.execute(f"SELECT COUNT(*) FROM {tname}")
    total = cur.fetchone()[0]
    print(f'\n=== {tname} ({total} rows) ===')
    print(f'Columns: {col_names}')
    cur.execute(f"SELECT * FROM {tname} LIMIT 3")
    rows = cur.fetchall()
    for r in rows:
        print(r)

conn.close()
