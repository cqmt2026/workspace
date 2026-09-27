#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""更新multi_channel_ledger.json"""
import json
import os
import sqlite3
import time

LEDGER = 'data/multi_channel_ledger.json'
DB = 'data/baidu_crm.db'

# 读取现有台账
with open(LEDGER, 'r', encoding='utf-8') as f:
    ledger = json.load(f)

# 更新metadata
ledger['metadata']['last_updated'] = '2026-08-30'
ledger['metadata']['version'] = '1.4'

# 从CRM重新统计各渠道行数
conn = sqlite3.connect(DB)
cur = conn.cursor()

# 高德POI统计
cur.execute("SELECT COUNT(*) FROM customers WHERE source LIKE '%高德%'")
amap_count = cur.fetchone()[0]
ledger['channels']['高德POI']['coverage']['row_count'] = amap_count
ledger['channels']['高德POI']['coverage']['last_updated'] = '2026-08-30'
ledger['channels']['高德POI']['status'] = '⚠️今日配额耗尽(月配额正常，明日0点恢复)'

# 百度POI统计
cur.execute("SELECT COUNT(*) FROM customers WHERE source LIKE '%百度%'")
baidu_count = cur.fetchone()[0]
ledger['channels']['百度POI']['coverage']['row_count'] = baidu_count
ledger['channels']['百度POI']['coverage']['last_updated'] = '2026-08-30'
ledger['channels']['百度POI']['status'] = '❌今日配额耗尽(需明日0点恢复)'

# 腾讯POI统计
cur.execute("SELECT COUNT(*) FROM customers WHERE source LIKE '%腾讯%'")
tx_count = cur.fetchone()[0]
ledger['channels']['腾讯POI']['coverage']['row_count'] = tx_count
ledger['channels']['腾讯POI']['coverage']['last_updated'] = '2026-08-30'
ledger['channels']['腾讯POI']['status'] = '❌今日配额耗尽(需明日0点恢复)'

conn.close()

# 更新覆盖摘要
total_rows = amap_count + baidu_count + tx_count + 1051 + 204 + 9 + 2280  # 加上政府官方数据
ledger['coverage_summary']['total_rows'] = total_rows
ledger['coverage_summary']['today_patch'] = {
    'source': '导入master已有补抓数据+百度POI紧急补抓',
    'rows': 292,
    'industries': ['人力资源','能源环保补充','电子科技']
}

with open(LEDGER, 'w', encoding='utf-8') as f:
    json.dump(ledger, f, ensure_ascii=False, indent=2)

print(f"台账已更新: 高德{amap_count}条, 百度{baidu_count}条, 腾讯{tx_count}条")
print(f"总行数: {total_rows}")
