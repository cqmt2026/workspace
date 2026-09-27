#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复电话清洗逻辑 - 保留有效座机和手机号"""
import sqlite3
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

DB = 'data/baidu_crm.db'

def clean_phone_v2(phone):
    """改进的电话清洗逻辑"""
    if not phone:
        return ''
    phone = str(phone).strip()
    
    # 提取所有数字
    digits = re.sub(r'\D', '', phone)
    
    # 手机号：11位，以1开头
    if len(digits) == 11 and digits.startswith('1'):
        return digits
    
    # 座机号：处理023-xxxxxxxx格式
    # 保留原始格式或提取纯数字
    if '-' in phone:
        # 023-63108016 格式，保留完整数字
        return digits
    
    # 纯数字座机（7-8位）
    if 7 <= len(digits) <= 8:
        return digits
    
    # 其他情况返回空
    return ''

def restore_phones():
    """从原始数据恢复电话"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    # 获取所有高德源数据
    cur.execute("""
        SELECT id, phone, source 
        FROM customers 
        WHERE source LIKE '%高德%' 
        AND (phone IS NULL OR phone = '' OR LENGTH(phone) < 7)
    """)
    rows = cur.fetchall()
    
    print(f"需要恢复{len(rows)}条电话记录...")
    
    restored = 0
    for cust_id, old_phone, source in rows:
        # 这里需要重新从原始CSV导入，暂时跳过
        pass
    
    # 先用改进的清洗逻辑重新处理现有数据
    cur.execute("SELECT id, phone FROM customers WHERE phone IS NOT NULL AND phone != ''")
    all_phones = cur.fetchall()
    
    print(f"\n重新清洗{len(all_phones)}条现有电话...")
    
    fixed = 0
    cleared = 0
    for cust_id, phone in all_phones:
        new_phone = clean_phone_v2(phone)
        if new_phone != phone:
            if new_phone:
                cur.execute("UPDATE customers SET phone=? WHERE id=?", (new_phone, cust_id))
                fixed += 1
            else:
                cur.execute("UPDATE customers SET phone='' WHERE id=?", (cust_id,))
                cleared += 1
    
    conn.commit()
    
    # 统计
    cur.execute("SELECT COUNT(*) FROM customers WHERE phone IS NOT NULL AND phone != ''")
    has_phone = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM customers")
    total = cur.fetchone()[0]
    
    conn.close()
    
    print(f"\n清洗结果:")
    print(f"  修复格式: {fixed}条")
    print(f"  清空无效: {cleared}条")
    print(f"  有效电话: {has_phone}/{total} ({round(has_phone/total*100,1)}%)")

if __name__ == '__main__':
    restore_phones()
