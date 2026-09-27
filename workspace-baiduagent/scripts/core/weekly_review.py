import sqlite3, json, sys
from datetime import datetime, timedelta

DB = 'data/baidu_crm.db'
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=== TABLES ===")
for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'"):
    print(r['name'])

print("\n=== CALL LOG SCHEMA ===")
for r in cur.execute("PRAGMA table_info(call_logs)"):
    print(dict(r))

print("\n=== CALL LOG SCHEMA (alt names) ===")
for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%call%'"):
    t = r['name']
    print("Table:", t)
    for c in cur.execute(f"PRAGMA table_info({t})"):
        print("  ", dict(c)['name'], dict(c)['type'])
