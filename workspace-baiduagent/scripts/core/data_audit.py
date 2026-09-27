# -*- coding: utf-8 -*-
"""
CRM数据完整性核查脚本
逐一检查每一条数据的完整性和质量问题
"""
import sqlite3
import json
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'data/baidu_crm.db'

def audit():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    print('=' * 70)
    print('【CRM数据完整性核查报告】')
    print(f'数据库: {DB_PATH}')
    print(f'核查时间: 2026-09-05 12:53')
    print('=' * 70)
    
    # 1. 基础统计
    c.execute('SELECT COUNT(*) FROM customers')
    total = c.fetchone()[0]
    print(f'\n📊 总客户数: {total}')
    
    # 2. 字段完整性检查
    issues = defaultdict(int)
    details = []
    
    # 检查每个字段
    c.execute('SELECT id, name, phone, district, industry, tier, lng, lat, source FROM customers')
    rows = c.fetchall()
    
    for row in rows:
        row_issues = []
        
        # 企业名称
        if not row['name'] or row['name'].strip() == '':
            issues['name_empty'] += 1
            row_issues.append('名称为空')
        
        # 联系电话
        if not row['phone'] or row['phone'].strip() == '':
            issues['phone_empty'] += 1
            row_issues.append('电话为空')
        
        # 所在区域
        if not row['district'] or row['district'].strip() == '':
            issues['district_empty'] += 1
            row_issues.append('区域为空')
        
        # 行业分类
        if not row['industry'] or row['industry'].strip() == '':
            issues['industry_empty'] += 1
            row_issues.append('行业为空')
        
        # 层级标签
        if not row['tier'] or row['tier'].strip() == '':
            issues['tier_empty'] += 1
            row_issues.append('层级为空')
        
        # 坐标
        if not row['lng'] or not row['lat']:
            issues['coord_empty'] += 1
            row_issues.append('坐标为空')
        
        # 记录有问题的行
        if row_issues:
            details.append({
                'id': row['id'],
                'name': row['name'],
                'issues': row_issues
            })
    
    # 3. 输出统计结果
    print('\n🔍 字段完整性统计:')
    print(f'  企业名称缺失: {issues["name_empty"]} ({issues["name_empty"]/total*100:.2f}%)')
    print(f'  联系电话缺失: {issues["phone_empty"]} ({issues["phone_empty"]/total*100:.2f}%)')
    print(f'  所在区域缺失: {issues["district_empty"]} ({issues["district_empty"]/total*100:.2f}%)')
    print(f'  行业分类缺失: {issues["industry_empty"]} ({issues["industry_empty"]/total*100:.2f}%)')
    print(f'  层级标签缺失: {issues["tier_empty"]} ({issues["tier_empty"]/total*100:.2f}%)')
    print(f'  坐标缺失: {issues["coord_empty"]} ({issues["coord_empty"]/total*100:.2f}%)')
    
    # 4. 有问题的行示例（前20条）
    print(f'\n⚠️ 有问题数据示例 (前20条):')
    for i, item in enumerate(details[:20], 1):
        print(f'  {i}. ID:{item["id"]} | {item["name"][:30]}... | {", ".join(item["issues"])}')
    
    # 5. 按行业分析电话覆盖率
    print('\n📈 各行业电话覆盖率分析:')
    c.execute('''
        SELECT industry, 
               COUNT(*) as total,
               SUM(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 ELSE 0 END) as has_phone
        FROM customers 
        GROUP BY industry 
        ORDER BY CAST(has_phone AS FLOAT)/total DESC
    ''')
    industries = c.fetchall()
    
    print(f'{"行业":<20} {"总数":<8} {"有电话":<8} {"覆盖率":<10} {"状态"}')
    print('-' * 60)
    for ind in industries:
        rate = ind['has_phone'] / ind['total'] * 100 if ind['total'] > 0 else 0
        status = '✅' if rate >= 50 else ('⚠️' if rate >= 20 else '❌')
        print(f'{ind["industry"]:<20} {ind["total"]:<8} {ind["has_phone"]:<8} {rate:>6.1f}%   {status}')
    
    # 6. 按区域分析
    print('\n📍 各区域数据分布:')
    c.execute('''
        SELECT district, 
               COUNT(*) as total,
               SUM(CASE WHEN phone IS NOT NULL AND phone != '' THEN 1 ELSE 0 END) as has_phone
        FROM customers 
        GROUP BY district 
        ORDER BY total DESC
    ''')
    districts = c.fetchall()
    
    print(f'{"区域":<15} {"总数":<8} {"有电话":<8} {"覆盖率":<10}')
    print('-' * 50)
    for d in districts[:15]:  # 只显示前15个区域
        rate = d['has_phone'] / d['total'] * 100 if d['total'] > 0 else 0
        print(f'{d["district"]:<15} {d["total"]:<8} {d["has_phone"]:<8} {rate:>6.1f}%')
    
    # 7. 层级分布
    print('\n🏷️ 层级标签分布:')
    c.execute('SELECT tier, COUNT(*) as count FROM customers GROUP BY tier')
    tiers = c.fetchall()
    for t in tiers:
        print(f'  {t["tier"] or "未分类"}: {t["count"]}家 ({t["count"]/total*100:.1f}%)')
    
    # 8. 数据来源分布
    print('\n📊 数据来源分布:')
    c.execute('SELECT source, COUNT(*) as count FROM customers GROUP BY source ORDER BY count DESC')
    sources = c.fetchall()
    for s in sources[:15]:
        print(f'  {s["source"] or "未知"}: {s["count"]}家')
    
    # 9. 异常值检查
    print('\n🚨 异常值检查:')
    
    # 检查重复企业
    c.execute('''
        SELECT name, COUNT(*) as cnt 
        FROM customers 
        GROUP BY name 
        HAVING cnt > 1
        LIMIT 10
    ''')
    duplicates = c.fetchall()
    if duplicates:
        print(f'  ⚠️ 发现重复企业名称 (前10个):')
        for d in duplicates:
            print(f'    - {d["name"]}: {d["cnt"]}条')
    else:
        print('  ✅ 未发现重复企业名称')
    
    # 检查电话号码格式
    c.execute('''
        SELECT id, name, phone 
        FROM customers 
        WHERE phone IS NOT NULL AND phone != ''
        AND LENGTH(phone) < 7
        LIMIT 10
    ''')
    short_phones = c.fetchall()
    if short_phones:
        print(f'  ⚠️ 发现短电话号码 (前10个):')
        for p in short_phones:
            print(f'    - {p["name"]}: {p["phone"]}')
    else:
        print('  ✅ 未发现短电话号码')
    
    # 检查无效坐标
    c.execute('''
        SELECT id, name, lat, lng
        FROM customers
        WHERE (lat IS NULL OR lng IS NULL)
           OR lat < -90 OR lat > 90
           OR lng < -180 OR lng > 180
        LIMIT 10
    ''')
    bad_coords = c.fetchall()
    if bad_coords:
        print(f'  ⚠️ 发现异常坐标 (前10个):')
        for b in bad_coords:
            print(f'    - {b["name"]}: lat={b["lat"]}, lng={b["lng"]}')
    else:
        print('  ✅ 未发现异常坐标')
    
    # 10. 汇总评分
    print('\n' + '=' * 70)
    print('【系统健康度评分】')
    print('=' * 70)
    
    score = 100
    deductions = []
    
    # 电话覆盖率扣分
    phone_rate = (total - issues['phone_empty']) / total * 100
    if phone_rate < 50:
        score -= 20
        deductions.append(f'电话覆盖率过低({phone_rate:.1f}%)')
    elif phone_rate < 70:
        score -= 10
        deductions.append(f'电话覆盖率偏低({phone_rate:.1f}%)')
    
    # 层级标签缺失扣分
    tier_rate = (total - issues['tier_empty']) / total * 100
    if tier_rate < 90:
        score -= 15
        deductions.append(f'层级标签缺失较多({tier_rate:.1f}%)')
    
    # 重复数据扣分
    if duplicates:
        score -= 10
        deductions.append('存在重复数据')
    
    # 通话记录扣分
    c.execute('SELECT COUNT(*) FROM call_logs')
    call_count = c.fetchone()[0]
    if call_count == 0:
        score -= 25
        deductions.append('无通话记录(业务未启动)')
    
    print(f'\n综合评分: {score}/100')
    print(f'\n扣分项:')
    for d in deductions:
        print(f'  - {d}')
    
    print('\n' + '=' * 70)
    print('【建议优先级】')
    print('=' * 70)
    
    if issues['phone_empty'] > 0:
        print(f'🔴 P0: 补充电话数据 ({issues["phone_empty"]}条缺失)')
        print('   建议: 企查查批量筛选、官网挖掘、行业协会名单')
    
    if issues['tier_empty'] > 0:
        print(f'🟡 P1: 完善层级标签 ({issues["tier_empty"]}条缺失)')
        print('   建议: 按行业+电话质量自动分配A/B类')
    
    if duplicates:
        print(f'🟡 P1: 清理重复数据 ({len(duplicates)}个重复名称)')
        print('   建议: 合并重复记录，保留最完整信息')
    
    if call_count == 0:
        print(f'🔴 P0: 启动电话拨打业务')
        print('   建议: 周一(9/7)正式启动，目标20-30通/天')
    
    conn.close()
    
    # 11. 导出详细问题列表
    if details:
        output_file = 'data/audit_issues.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total': total,
                'issue_count': len(details),
                'issues_summary': dict(issues),
                'details': details[:100]  # 只导出前100条详细问题
            }, f, ensure_ascii=False, indent=2)
        print(f'\n💾 详细问题列表已导出: {output_file}')

if __name__ == '__main__':
    audit()
