#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从原始CSV重新导入高德数据以恢复电话"""
import csv
import sqlite3
import re
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

DB = 'data/baidu_crm.db'
SOURCE_DIR = 'data/source/amap'

def clean_phone(phone):
    """清洗电话"""
    if not phone:
        return ''
    phone = str(phone).strip()
    digits = re.sub(r'\D', '', phone)
    
    # 手机号
    if len(digits) == 11 and digits.startswith('1'):
        return digits
    
    # 座机（含区号）
    if len(digits) >= 7:
        return digits
    
    return ''

def import_amap_data():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    # 高德CSV文件列表
    amap_files = {
        '口腔诊所': 'kq_list_chongqing_amap_20260828.csv',
        '医美机构': 'my_list_chongqing_amap_20260828.csv',
        '教培机构': 'jp_list_chongqing_amap_20260828.csv',
        '宠物医院': 'ym_list_chongqing_amap_20260828.csv',
        '装修装饰': 'zs_list_chongqing_amap_20260828.csv',
        '酒店餐饮': 'cw_list_chongqing_amap_20260828.csv',
    }
    
    total_added = 0
    total_updated = 0
    
    for industry, filename in amap_files.items():
        filepath = os.path.join(SOURCE_DIR, filename)
        if not os.path.exists(filepath):
            print(f"  跳过: {filename} (文件不存在)")
            continue
        
        rows = list(csv.DictReader(open(filepath, encoding='utf-8-sig')))
        print(f"\n处理{industry}: {len(rows)}条")
        
        for row in rows:
            name = row.get('机构名称', '').strip()
            if not name:
                continue
            
            # 清洗电话
            raw_phone = row.get('电话', '')
            phone = clean_phone(raw_phone)
            
            # 检查是否已存在
            cur.execute("SELECT id FROM customers WHERE name = ?", (name,))
            existing = cur.fetchone()
            
            if existing:
                # 更新电话
                if phone and (not existing or existing[0]):
                    cur.execute("UPDATE customers SET phone=? WHERE id=?", (phone, existing[0]))
                    if cur.rowcount:
                        total_updated += 1
            else:
                # 插入新记录
                district = row.get('区域', '')
                address = row.get('地址', '')
                lat = row.get('纬度', '')
                lng = row.get('经度', '')
                
                cur.execute("""
                    INSERT OR IGNORE INTO customers 
                    (name, industry, phone, address, district, lat, lng, source, status, tier, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, '待联系', 'B', datetime('now','localtime'))
                """, (
                    name, industry, phone, address, district, lat, lng,
                    f"高德POI-{industry}"
                ))
                if cur.rowcount:
                    total_added += 1
    
    conn.commit()
    
    # 统计
    cur.execute("SELECT COUNT(*) FROM customers")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM customers WHERE phone IS NOT NULL AND phone != ''")
    has_phone = cur.fetchone()[0]
    
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"导入完成:")
    print(f"  新增客户: {total_added}条")
    print(f"  更新电话: {total_updated}条")
    print(f"  CRM总数: {total:,}")
    print(f"  有电话: {has_phone:,} ({round(has_phone/total*100,1)}%)")

if __name__ == '__main__':
    import_amap_data()
