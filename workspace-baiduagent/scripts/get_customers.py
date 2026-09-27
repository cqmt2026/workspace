#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""获取Top10今日拨打客户及话术匹配"""
import sqlite3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'baidu_crm.db')
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 获取各行业A类客户，按优先级排序
cur.execute("""
    SELECT id, name, industry, tier, phone, status, last_call, district
    FROM customers
    WHERE tier = 'A'
    ORDER BY
        CASE
            WHEN industry = '医疗器械' THEN 1
            WHEN industry = '新材料' THEN 2
            WHEN industry = '机械装备' THEN 3
            WHEN industry = '环保检测' THEN 4
            WHEN industry = '新能源' THEN 5
            WHEN industry = '建筑建材' THEN 6
            ELSE 7
        END,
        last_call IS NULL DESC,
        last_call ASC,
        name
    LIMIT 50
""")
rows = cur.fetchall()

for r in rows:
    print(f"{r[0]}|{r[1]}|{r[2]}|{r[3]}|{r[4]}|{r[5]}|{r[6]}|{r[7]}")

conn.close()
