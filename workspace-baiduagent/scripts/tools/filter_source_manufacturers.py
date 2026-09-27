#!/usr/bin/env python3
"""筛选源头厂家（排除批发商）"""
import sqlite3
import os
import json
import sys

DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'

# 排除关键词：批发商、贸易商、代理商等
EXCLUDE_KEYWORDS = ['批发', '超市', '商行', '经销', '代理', '贸易', '供应站', '零售', '门店', '经营部', '供销']

def exclude_pattern():
    """生成SQL排除条件"""
    conditions = [f"name NOT LIKE '%{kw}%'" for kw in EXCLUDE_KEYWORDS]
    return ' AND '.join(conditions)

def query_customers(industry, limit=15):
    """查询指定行业的源头厂家"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    pattern = exclude_pattern()
    cur.execute(f'''
        SELECT name, industry, phone, tier, district 
        FROM customers
        WHERE industry = ? AND tier = 'A' AND phone IS NOT NULL AND phone != ''
        AND {pattern}
        ORDER BY 
            CASE WHEN district IS NOT NULL AND district != '' THEN 0 ELSE 1 END,
            district, name
        LIMIT ?
    ''', (industry, limit))
    rows = cur.fetchall()
    conn.close()
    return rows

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
    
    # 查询各行业的源头厂家
    industries = [
        '机械装备汽配',
        '医疗器械',
        '新材料化工',
        '环保检测',
        '智能制造',
        '自动化设备',
        '液压设备',
        '精密机械',
        '数控机床',
        '模具',
    ]
    
    print('=' * 80)
    print('【源头厂家筛选结果】（已排除批发商）')
    print('=' * 80)
    
    for industry in industries:
        rows = query_customers(industry, limit=10)
        if rows:
            print(f'\n【{industry}】共找到 {len(rows)} 家源头厂家')
            print('-' * 80)
            for i, (name, ind, phone, tier, district) in enumerate(rows, 1):
                d = district if district else '未知'
                # 清理电话格式
                phone_clean = phone.replace('(', '').replace(')', '').replace('-', '')[:15]
                print(f'  {i:2}. {name[:30]:<30} | {phone_clean:<18} | {d}')
    
    # 统计总数
    print('\n' + '=' * 80)
    print('【汇总统计】')
    print('=' * 80)
    
    total = 0
    for industry in industries:
        rows = query_customers(industry, limit=100)
        total += len(rows)
        print(f'{industry}: {len(rows)} 家')
    
    print(f'\n总计: {total} 家源头厂家')

if __name__ == '__main__':
    main()
