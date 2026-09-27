#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据质量验证工具
交付前必须验证数据质量
"""
import sqlite3
import sys

DB_PATH = 'data/baidu_crm.db'

# 已知无效行业列表（需过滤）
INVALID_INDUSTRIES = ['宠物医院']

def validate_data():
    """验证数据质量"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    results = {
        'total': 0,
        'has_phone': 0,
        'invalid_industry': 0,
        'quality_issues': []
    }
    
    # 总客户数
    c.execute('SELECT COUNT(*) FROM customers')
    results['total'] = c.fetchone()[0]
    
    # 有电话数
    c.execute('SELECT COUNT(*) FROM customers WHERE phone IS NOT NULL AND phone != ""')
    results['has_phone'] = c.fetchone()[0]
    
    # 无效行业数量
    for industry in INVALID_INDUSTRIES:
        c.execute('SELECT COUNT(*) FROM customers WHERE industry = ?', (industry,))
        count = c.fetchone()[0]
        if count > 0:
            results['invalid_industry'] += count
            results['quality_issues'].append(f'{industry}: {count}家')
    
    # 电话格式问题（含分号）
    c.execute("SELECT COUNT(*) FROM customers WHERE phone LIKE '%;%'")
    semicolon_count = c.fetchone()[0]
    if semicolon_count > 0:
        results['quality_issues'].append(f'电话含分号: {semicolon_count}家')
    
    # 电话格式问题（含空格）
    c.execute("SELECT COUNT(*) FROM customers WHERE phone LIKE '% %'")
    space_count = c.fetchone()[0]
    if space_count > 0:
        results['quality_issues'].append(f'电话含空格: {space_count}家')
    
    # 地址为空
    c.execute('SELECT COUNT(*) FROM customers WHERE address IS NULL OR address = ""')
    empty_address = c.fetchone()[0]
    if empty_address > 0:
        results['quality_issues'].append(f'地址为空: {empty_address}家')
    
    conn.close()
    
    return results

def print_report(results):
    """打印验证报告"""
    print("=" * 60)
    print("[数据质量验证报告]")
    print("=" * 60)
    print()
    print(f"总客户数: {results['total']}家")
    print(f"有电话数: {results['has_phone']}家 ({results['has_phone']/results['total']*100:.1f}%)")
    print(f"无效行业: {results['invalid_industry']}家")
    print()
    
    if results['quality_issues']:
        print("[!] 数据质量问题:")
        for issue in results['quality_issues']:
            print(f"  - {issue}")
        print()
        print("建议: 生成清单前过滤这些问题")
    else:
        print("[OK] 数据质量良好")
    
    print()
    print("=" * 60)

if __name__ == '__main__':
    results = validate_data()
    print_report(results)
    
    # 返回退出码
    sys.exit(0 if not results['quality_issues'] else 1)
