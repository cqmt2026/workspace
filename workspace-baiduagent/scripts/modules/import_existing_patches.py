#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""导入master目录中已有的补抓数据到CRM"""
import csv
import os
import sqlite3

DB = 'data/baidu_crm.db'
MASTER = 'data/master'

# 低覆盖率行业的master文件
FILES = {
    '人力资源': '人力资源_baidu.csv',
    '检验检测': '检验检测_baidu.csv',
    '物流货运': '物流货运_baidu.csv',
    '软件信息': '软件信息_baidu.csv',
    '智能制造': '智能制造_baidu.csv',
    '能源环保补充': '能源环保补充_baidu.csv',
    '食品加工': '食品加工_baidu.csv',
    '电子科技': '电子科技_baidu.csv',
}

conn = sqlite3.connect(DB)
cur = conn.cursor()

total_inserted = 0
total_skipped = 0
total_phones = 0

print("="*60)
print("【导入已有补抓数据到CRM】")
print("="*60)

for industry, filename in FILES.items():
    fp = os.path.join(MASTER, filename)
    if not os.path.exists(fp):
        print(f"\n⚠️ {industry}: 文件不存在 {fp}")
        continue
    
    rows = list(csv.DictReader(open(fp, encoding='utf-8-sig')))
    inserted = 0
    skipped = 0
    phones = 0
    
    for row in rows:
        name = row.get('机构名称','').strip()
        if not name:
            continue
        
        # Check if exists
        cur.execute("SELECT id FROM customers WHERE name = ?", (name,))
        if cur.fetchone():
            skipped += 1
            continue
        
        tel = row.get('电话','').strip()
        if tel:
            tel = ''.join(c for c in tel if c.isdigit())
            if len(tel) < 7:
                tel = ''
        if tel:
            phones += 1
        
        district = row.get('区域','') or row.get('area','') or ''
        lat = row.get('纬度','') or row.get('lat','') or ''
        lng = row.get('经度','') or row.get('lng','') or ''
        
        cur.execute("""
            INSERT INTO customers (name, industry, phone, address, district, lat, lng, source, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
        """, (
            name, industry, tel, row.get('地址',''), district, lat, lng,
            f"百度POI补抓-{industry}", '待联系'
        ))
        inserted += cur.rowcount
    
    conn.commit()
    total_inserted += inserted
    total_skipped += skipped
    total_phones += phones
    
    pct = round(phones/len(rows)*100,1) if rows else 0
    print(f"  {industry}: +{inserted}条(电话{phones}/{len(rows)}={pct}%), 跳过{skipped}条")

# 也导入complete文件
for f in sorted(os.listdir(MASTER)):
    if '_complete' in f:
        fp = os.path.join(MASTER, f)
        rows = list(csv.DictReader(open(fp, encoding='utf-8-sig')))
        inserted = 0
        skipped = 0
        phones = 0
        industry = f.replace('_complete_baidu.csv','').replace('_complete_amap.csv','')
        for row in rows:
            name = row.get('机构名称','').strip()
            if not name:
                continue
            cur.execute("SELECT id FROM customers WHERE name = ?", (name,))
            if cur.fetchone():
                skipped += 1
                continue
            tel = row.get('电话','').strip()
            if tel:
                tel = ''.join(c for c in tel if c.isdigit())
                if len(tel) < 7:
                    tel = ''
            if tel:
                phones += 1
            cur.execute("""
                INSERT INTO customers (name, industry, phone, address, district, lat, lng, source, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
            """, (
                name, industry, tel, row.get('地址',''), row.get('区域',''),
                row.get('纬度',''), row.get('经度',''), f"百度POI彻底补抓-{industry}", '待联系'
            ))
            inserted += cur.rowcount
        conn.commit()
        total_inserted += inserted
        total_skipped += skipped
        total_phones += phones
        if rows:
            print(f"  {f}: +{inserted}条(电话{phones}/{len(rows)}), 跳过{skipped}条")

conn.close()

# 最终统计
conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM customers')
total = cur.fetchone()[0]
cur.execute('SELECT COUNT(*) FROM customers WHERE phone IS NOT NULL AND phone != ""')
has_phone = cur.fetchone()[0]
conn.close()

print(f"\n{'='*60}")
print(f"【导入完成】")
print(f"本次新增: {total_inserted}条 (含电话{total_phones}条)")
print(f"CRM总客户: {total:,}")
print(f"有电话: {has_phone:,} ({round(has_phone/total*100,1)}%)")
