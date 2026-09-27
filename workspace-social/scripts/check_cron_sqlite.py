import sqlite3

db = r'C:\Users\Administrator\.openclaw\state\openclaw.sqlite'
conn = sqlite3.connect(db)
cur = conn.cursor()

# Check cron_jobs table structure
cur.execute("PRAGMA table_info(cron_jobs)")
cols = cur.fetchall()
print("cron_jobs columns:", cols)

# Check enabled jobs
cur.execute('SELECT COUNT(*) FROM cron_jobs WHERE enabled = 1')
print("Enabled jobs:", cur.fetchone()[0])

# Sample a few jobs
cur.execute('SELECT id, name, enabled FROM cron_jobs LIMIT 5')
rows = cur.fetchall()
for r in rows:
    print(f"  {r[0][:8]} | enabled={r[2]} | {r[1][:50]}")

conn.close()
