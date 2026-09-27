import sqlite3
conn = sqlite3.connect(r'data/factors.db')
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print('Tables:', [t[0] for t in tables])
for t in tables:
    cols = conn.execute("PRAGMA table_info([{}])".format(t[0])).fetchall()
    print('  {}: {}'.format(t[0], [(c[1],c[2]) for c in cols]))
    count = conn.execute("SELECT COUNT(*) FROM [{}]".format(t[0])).fetchone()[0]
    print('    rows: {}'.format(count))
conn.close()