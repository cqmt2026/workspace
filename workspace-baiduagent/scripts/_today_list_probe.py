import sqlite3, os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
conn = sqlite3.connect('data/baidu_crm.db')
cur = conn.cursor()
cur.execute('SELECT name FROM sqlite_master WHERE type="table"')
print("TABLES:", cur.fetchall())
for (t,) in cur.execute('SELECT name FROM sqlite_master WHERE type="table"').fetchall():
    try:
        cur.execute(f'PRAGMA table_info({t})')
        print(t, "COLS:", [r[1] for r in cur.fetchall()])
        cur.execute(f'SELECT COUNT(*) FROM {t}')
        print("  rows:", cur.fetchone()[0])
    except Exception as e:
        print(t, "ERR", e)