#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""完善数据清洗 - 补全区域信息"""
import sqlite3
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

DB = 'data/baidu_crm.db'

DISTRICTS = ['渝中区', '江北区', '南岸区', '九龙坡区', '沙坪坝区', 
             '北碚区', '大渡口区', '巴南区', '高新区', '两江新区']

def extract_district(address):
    """从地址中提取区域"""
    if not address:
        return ''
    for dist in DISTRICTS:
        if dist in address:
            return dist
    return ''

def clean_data_v2():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    # 获取所有需要补全区域的客户
    cur.execute("SELECT id, address, district FROM customers WHERE district IS NULL OR district = ''")
    customers = cur.fetchall()
    
    print(f"开始补全{len(customers)}条客户区域信息...")
    
    updated = 0
    for cust_id, address, old_district in customers:
        if address:
            district = extract_district(address)
            if district and district != old_district:
                cur.execute("UPDATE customers SET district=? WHERE id=?", (district, cust_id))
                updated += cur.rowcount
    
    conn.commit()
    
    # 统计
    cur.execute("SELECT COUNT(*) FROM customers WHERE district IS NOT NULL AND district != ''")
    has_district = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM customers")
    total = cur.fetchone()[0]
    
    conn.close()
    
    print(f"\n=== 补全结果 ===")
    print(f"总客户数: {total:,}")
    print(f"有区域: {has_district:,} ({round(has_district/total*100,1)}%)")
    print(f"本次补全: {updated}条")

if __name__ == '__main__':
    clean_data_v2()
