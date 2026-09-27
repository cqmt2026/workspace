# -*- coding: utf-8 -*-
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent.parent / "data" / "pv.db"
conn = sqlite3.connect(str(db_path))
cur = conn.cursor()

# Get table schema
cur.execute("PRAGMA table_info(hot_topics)")
cols = [col[1] for col in cur.fetchall()]
print(f"Columns: {cols}")

# Total count
cur.execute("SELECT COUNT(*) FROM hot_topics")
total = cur.fetchone()[0]
print(f"Total topics: {total}")

# PV-related count
cur.execute("""
    SELECT COUNT(*) FROM hot_topics 
    WHERE title LIKE '%光伏%' OR title LIKE '%太阳能%' OR title LIKE '%并网%' 
    OR title LIKE '%分布式%' OR title LIKE '%组件%' OR title LIKE '%电站%'
""")
pv_count = cur.fetchone()[0]
print(f"PV-related topics: {pv_count}")

# Latest PV topics
cur.execute("""
    SELECT id, source, title, collected_at 
    FROM hot_topics 
    WHERE title LIKE '%光伏%' OR title LIKE '%太阳能%' OR title LIKE '%并网%'
    ORDER BY collected_at DESC LIMIT 10
""")
print("\nLatest PV topics:")
for row in cur.fetchall():
    print(f"  [{row[1]}] {row[2][:50]}... ({row[3][:10]})")

# By source
cur.execute("SELECT source, COUNT(*) FROM hot_topics GROUP BY source ORDER BY COUNT(*) DESC")
print("\nBy source:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

conn.close()
