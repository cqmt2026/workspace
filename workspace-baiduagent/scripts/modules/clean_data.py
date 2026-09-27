#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据清洗脚本 - 清理电话号码、地址等"""
import sqlite3
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

DB = 'data/baidu_crm.db'

def clean_phone(phone):
    """清理电话号码"""
    if not phone:
        return ''
    # 移除所有非数字字符
    digits = re.sub(r'\D', '', str(phone))
    # 过滤无效号码
    if len(digits) < 7 or len(digits) > 15:
        return ''
    # 移除开头的0（座机）
    if digits.startswith('0') and len(digits) == 11:
        digits = digits[1:]
    return digits

def clean_address(addr):
    """清理地址，提取区域"""
    if not addr:
        return ''
    # 移除多余空格
    addr = re.sub(r'\s+', ' ', addr.strip())
    return addr

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

def clean_data():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    # 获取所有客户
    cur.execute("SELECT id, phone, address, district FROM customers")
    customers = cur.fetchall()
    
    print(f"开始清洗{len(customers)}条客户数据...")
    
    updated_phone = 0
    updated_address = 0
    updated_district = 0
    fixed_phone = 0
    
    for cust_id, phone, address, district in customers:
        # 清洗电话
        if phone:
            clean_p = clean_phone(phone)
            if clean_p != phone:
                phone = clean_p
                fixed_phone += 1
            if clean_p and len(clean_p) < 7:
                phone = ''  # 无效号码清空
        elif phone is None:
            phone = ''
        
        # 清洗地址
        if address:
            clean_a = clean_address(address)
            if clean_a != address:
                address = clean_a
                updated_address += 1
            
            # 提取区域
            if not district or district == '':
                extracted = extract_district(address)
                if extracted:
                    district = extracted
                    updated_district += 1
        
        # 更新数据库
        if phone != (cur.execute("SELECT phone FROM customers WHERE id=?", (cust_id,)).fetchone()[0] or ''):
            cur.execute("UPDATE customers SET phone=? WHERE id=?", (phone, cust_id))
            updated_phone += 1
        if address and address != (cur.execute("SELECT address FROM customers WHERE id=?", (cust_id,)).fetchone()[0] or ''):
            cur.execute("UPDATE customers SET address=? WHERE id=?", (address, cust_id))
        
        if district and district != (cur.execute("SELECT district FROM customers WHERE id=?", (cust_id,)).fetchone()[0] or ''):
            cur.execute("UPDATE customers SET district=? WHERE id=?", (district, cust_id))
    
    conn.commit()
    
    # 统计结果
    cur.execute("SELECT COUNT(*) FROM customers WHERE phone IS NOT NULL AND phone != ''")
    has_phone = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM customers WHERE district IS NOT NULL AND district != ''")
    has_district = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM customers")
    total = cur.fetchone()[0]
    
    conn.close()
    
    print(f"\n=== 清洗结果 ===")
    print(f"总客户数: {total:,}")
    print(f"有电话: {has_phone:,} ({round(has_phone/total*100,1)}%)")
    print(f"有区域: {has_district:,} ({round(has_district/total*100,1)}%)")
    print(f"\n清洗详情:")
    print(f"  修复电话号码: {fixed_phone}条")
    print(f"  更新地址格式: {updated_address}条")
    print(f"  补全区域信息: {updated_district}条")

if __name__ == '__main__':
    clean_data()
