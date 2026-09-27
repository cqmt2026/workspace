#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""更新台账和MEMORY.md"""
import json
import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 更新台账
LEDGER = 'data/multi_channel_ledger.json'
with open(LEDGER, 'r', encoding='utf-8') as f:
    ledger = json.load(f)

ledger['metadata']['last_updated'] = '2026-08-30'
ledger['metadata']['version'] = '1.5'

# 从CRM统计
conn = sqlite3.connect('data/baidu_crm.db')
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM customers WHERE source LIKE '%高德%'")
ledger['channels']['高德POI']['coverage']['row_count'] = cur.fetchone()[0]
ledger['channels']['高德POI']['status'] = '⚠️今日配额耗尽(需明日0点恢复)'

cur.execute("SELECT COUNT(*) FROM customers WHERE source LIKE '%百度%'")
ledger['channels']['百度POI']['coverage']['row_count'] = cur.fetchone()[0]
ledger['channels']['百度POI']['status'] = '❌今日配额耗尽(需明日0点恢复)'

cur.execute("SELECT COUNT(*) FROM customers WHERE source LIKE '%腾讯%'")
ledger['channels']['腾讯POI']['coverage']['row_count'] = cur.fetchone()[0]

conn.close()

total = ledger['channels']['高德POI']['coverage']['row_count'] + \
        ledger['channels']['百度POI']['coverage']['row_count'] + \
        ledger['channels']['腾讯POI']['coverage']['row_count'] + 1051 + 204 + 9 + 2280
ledger['coverage_summary']['total_rows'] = total
ledger['coverage_summary']['today_patch'] = {'source': '导入master已有补抓数据', 'rows': 292}

with open(LEDGER, 'w', encoding='utf-8') as f:
    json.dump(ledger, f, ensure_ascii=False, indent=2)

print(f"台账已更新: 总行数{total:,}")
