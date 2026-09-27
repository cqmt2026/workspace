# -*- coding: utf-8 -*-
import sys, os
from pathlib import Path
BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE / "scripts"))
os.chdir(str(BASE))

from core.database import PVDatabase

db = PVDatabase()

print("=" * 55)
print("Solar PV System - DB Status")
print("=" * 55)

# Policies
print("\n[Policies]")
policies = db.get_latest_policies(15)
for p in policies:
    print(f"  [{p['level']}] {p['title'][:55]}")
print(f"  Total: {len(policies)}")

# Hot topics (pv related)
print("\n[Hot Topics - PV related]")
topics = db.get_latest_pv_topics(20)
for t in topics:
    print(f"  [{t['source']}] {t['title'][:55]} (hot={t['hot_score']}, pv={t['pv_score']})")
print(f"  Total PV: {len(topics)}")

# Analysis
analysis = db.get_pv_analysis()
print(f"\n[Analysis]")
print(f"  Today PV topics: {analysis['today_pv_topics']}")
print(f"  Policies (7d): {analysis['policy_count']}")
print(f"  Competitors: {analysis['competitor_count']}")
print(f"  Sources: {analysis.get('sources', {})}")

db.close()
print("\n" + "=" * 55)
