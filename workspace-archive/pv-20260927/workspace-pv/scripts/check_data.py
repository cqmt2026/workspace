# -*- coding: utf-8 -*-
import sqlite3
from pathlib import Path

BASE = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-pv')
conn = sqlite3.connect(str(BASE / 'data' / 'pv.db'))
c = conn.cursor()

c.execute("SELECT title, source, pv_score FROM hot_topics WHERE pv_related=1 ORDER BY collected_at DESC LIMIT 10")
topics = c.fetchall()
print(f'Topics: {len(topics)}')
for t in topics:
    print(f'  [{t[1]}] {t[0][:50]} (score={t[2]})')

c.execute('SELECT title, level, province FROM policies ORDER BY collected_at DESC LIMIT 5')
policies = c.fetchall()
print(f'Policies: {len(policies)}')
for p in policies:
    print(f'  [{p[1]}] {p[0][:50]} (prov={p[2]})')

conn.close()
