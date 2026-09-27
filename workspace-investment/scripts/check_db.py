import sqlite3
conn = sqlite3.connect(r'F:\market_data.db')
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print([t[0] for t in tables])
conn.close()

# Check latest date
conn2 = sqlite3.connect(r'F:\market_data.db')
tables2 = conn2.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
for t in tables2:
    try:
        cnt = conn2.execute(f"SELECT COUNT(*) FROM [{t[0]}]").fetchone()[0]
        print(f"  {t[0]}: {cnt} rows")
    except Exception as e:
        print(f"  {t[0]}: ERROR {e}")
conn2.close()
