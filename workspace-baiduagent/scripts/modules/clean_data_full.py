#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""完善数据清洗 - 改进区域提取"""
import sqlite3
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

DB = 'data/baidu_crm.db'

# 区域关键词映射（更全面的匹配）
DISTRICT_PATTERNS = {
    '渝中区': ['渝中', '解放碑', '朝天门', '大坪', '两路口'],
    '江北区': ['江北', '观音桥', '北城天街', '红旗河沟', '冉家坝'],
    '南岸区': ['南岸', '南坪', '弹子石', '珊瑚路', '学府大道'],
    '九龙坡区': ['九龙坡', '杨家坪', '谢家湾', '石桥铺', '大渡口'],
    '沙坪坝区': ['沙坪坝', '三峡广场', '小龙坎', '新桥', '磁器口'],
    '北碚区': ['北碚', '碚城', '两江新区'],
    '大渡口区': ['大渡口', '九宫庙', '茄子溪'],
    '巴南区': ['巴南', '龙洲湾', '鱼洞', '界石'],
    '高新区': ['高新', '西永', '科学城', '悦来'],
    '渝北区': ['渝北', '两路', '回兴', '汽博', '照母山'],
}

def extract_district(address):
    """从地址中提取区域"""
    if not address:
        return ''
    addr_lower = address.lower()
    
    # 先匹配标准区域名
    for dist, keywords in DISTRICT_PATTERNS.items():
        for kw in keywords:
            if kw in address:
                return dist
    
    return ''

def clean_all():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    # 获取所有需要处理的数据
    cur.execute("SELECT id, address, district, phone FROM customers")
    customers = cur.fetchall()
    
    print(f"开始全面清洗{len(customers)}条数据...")
    
    stats = {
        'phone_fixed': 0,
        'phone_invalid': 0,
        'district_filled': 0,
        'address_cleaned': 0,
    }
    
    for cust_id, phone, district, address in customers:
        changes = []
        
        # 1. 清洗电话
        if phone:
            digits = re.sub(r'\D', '', str(phone))
            if len(digits) >= 7 and len(digits) <= 15:
                new_phone = digits
                if new_phone != str(phone):
                    changes.append(('phone', new_phone))
                    stats['phone_fixed'] += 1
            else:
                changes.append(('phone', ''))
                stats['phone_invalid'] += 1
        elif phone is None:
            changes.append(('phone', ''))
        
        # 2. 补全区域
        if not district or district == '':
            if address:
                new_dist = extract_district(address)
                if new_dist:
                    changes.append(('district', new_dist))
                    stats['district_filled'] += 1
        
        # 3. 清洗地址格式
        if address:
            clean_addr = re.sub(r'\s+', ' ', address.strip())
            if clean_addr != address:
                changes.append(('address', clean_addr))
                stats['address_cleaned'] += 1
        
        # 执行更新
        for field, value in changes:
            cur.execute(f"UPDATE customers SET {field}=? WHERE id=?", (value, cust_id))
    
    conn.commit()
    
    # 统计结果
    cur.execute("SELECT COUNT(*) FROM customers")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM customers WHERE phone IS NOT NULL AND phone != ''")
    has_phone = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM customers WHERE district IS NOT NULL AND district != ''")
    has_district = cur.fetchone()[0]
    
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"【数据清洗完成】")
    print(f"{'='*60}")
    print(f"总客户数: {total:,}")
    print(f"有电话: {has_phone:,} ({round(has_phone/total*100,1)}%)")
    print(f"有区域: {has_district:,} ({round(has_district/total*100,1)}%)")
    print(f"\n清洗统计:")
    print(f"  修复电话号码: {stats['phone_fixed']}条")
    print(f"  标记无效号码: {stats['phone_invalid']}条")
    print(f"  补全区域信息: {stats['district_filled']}条")
    print(f"  清洗地址格式: {stats['address_cleaned']}条")

if __name__ == '__main__':
    clean_all()
