# -*- coding: utf-8 -*-
import sqlite3, os

db = r'F:\market_data.db'
conn = sqlite3.connect(db)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('Tables:', tables)

for t in tables:
    tname = t[0]
    cursor.execute(f"SELECT COUNT(*) FROM [{tname}]")
    cnt = cursor.fetchone()[0]
    print(f'  {tname}: {cnt} rows')
    cursor.execute(f"PRAGMA table_info([{tname}])")
    cols = cursor.fetchall()
    print(f'  Columns: {[c[1] for c in cols]}')

conn.close()
