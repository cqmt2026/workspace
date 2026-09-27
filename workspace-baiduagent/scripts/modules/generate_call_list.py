# -*- coding: utf-8 -*-
"""
生成机械行业P0-P2拨打清单
按优先级排序，优先拨打有电话的主城区企业
"""
import sys, sqlite3, json
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/baidu_crm.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

print('='*70)
print('[Mechanical Industry Call List Generation - P0 to P2]')
print('='*70)
print(f'Generation time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('='*70)

# Query P0-P2 customers with phone, ordered by priority
print('\n[Step 1] Fetching P0-P2 customers with phone...')
c.execute('''
    SELECT id, name, industry, district, district_priority, phone, address, lat, lng
    FROM customers
    WHERE (industry LIKE '%机械%' OR industry = '液压设备' 
           OR industry = '工程机械' OR industry = '数控机床'
           OR industry = '精密机械' OR industry = '自动化设备')
      AND district_priority IN ('P0', 'P1', 'P2')
      AND phone IS NOT NULL
      AND phone != ''
    ORDER BY 
        CASE district_priority 
            WHEN 'P0' THEN 1 
            WHEN 'P1' THEN 2 
            WHEN 'P2' THEN 3 
        END,
        district,
        industry
''')
rows = c.fetchall()
print(f'  Total P0-P2 with phone: {len(rows)}')

# Group by priority and district
p0_list = [r for r in rows if r['district_priority'] == 'P0']
p1_list = [r for r in rows if r['district_priority'] == 'P1']
p2_list = [r for r in rows if r['district_priority'] == 'P2']

print(f'\n  P0 (Main urban): {len(p0_list)}')
print(f'  P1 (Suburban): {len(p1_list)}')
print(f'  P2 (Other districts): {len(p2_list)}')

# Generate call list
call_list = []
seq = 1

# P0 customers
for r in p0_list:
    call_list.append({
        'seq': seq,
        'priority': 'P0',
        'id': r['id'],
        'name': r['name'],
        'industry': r['industry'],
        'district': r['district'],
        'phone': r['phone'],
        'address': r['address'],
        'script': f'重庆{r["industry"]}百度几乎无投放，{r["district"]}区域蓝海。你们在百度能搜到吗？'
    })
    seq += 1

# P1 customers
for r in p1_list:
    call_list.append({
        'seq': seq,
        'priority': 'P1',
        'id': r['id'],
        'name': r['name'],
        'industry': r['industry'],
        'district': r['district'],
        'phone': r['phone'],
        'address': r['address'],
        'script': f'重庆{r["industry"]}百度几乎无投放，{r["district"]}区域蓝海。你们在百度能搜到吗？'
    })
    seq += 1

# P2 customers
for r in p2_list:
    call_list.append({
        'seq': seq,
        'priority': 'P2',
        'id': r['id'],
        'name': r['name'],
        'industry': r['industry'],
        'district': r['district'],
        'phone': r['phone'],
        'address': r['address'],
        'script': f'重庆{r["industry"]}百度几乎无投放，{r["district"]}区域蓝海。你们在百度能搜到吗？'
    })
    seq += 1

# Save to JSON
output_file = f'assets/机械行业拨打清单_P0P1P2_{datetime.now().strftime("%Y%m%d")}.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump({
        'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total': len(call_list),
        'p0_count': len(p0_list),
        'p1_count': len(p1_list),
        'p2_count': len(p2_list),
        'customers': call_list
    }, f, ensure_ascii=False, indent=2)
print(f'\n💾 Call list saved: {output_file}')

# Generate Markdown report
md_file = f'assets/机械行业拨打清单_P0P1P2_{datetime.now().strftime("%Y%m%d")}.md'
with open(md_file, 'w', encoding='utf-8') as f:
    f.write('# 机械行业拨打清单 (P0-P2)\n\n')
    f.write(f'> 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
    f.write(f'> 数据来源：百度POI补抓 + 高德POI\n')
    f.write(f'> 优先级：P0(主城区) > P1(近郊) > P2(其他区县)\n\n')
    
    f.write('## 📊 总体统计\n\n')
    f.write('| 优先级 | 区域范围 | 数量 | 占比 |\n')
    f.write(f'|--------|---------|------|------|\n')
    f.write(f'| P0 | 主城区9区+高新区+两江新区 | {len(p0_list)} | {len(p0_list)/len(call_list)*100:.1f}% |\n')
    f.write(f'| P1 | 璧山/江津/合川/永川/大足/铜梁 | {len(p1_list)} | {len(p1_list)/len(call_list)*100:.1f}% |\n')
    f.write(f'| P2 | 綦江/南川/长寿/荣昌等 | {len(p2_list)} | {len(p2_list)/len(call_list)*100:.1f}% |\n')
    f.write(f'| **总计** | - | **{len(call_list)}** | **100%** |\n\n')
    
    f.write('## 🎯 P0 主城区客户（优先拨打）\n\n')
    f.write('| # | 企业名称 | 行业 | 区域 | 电话 | 话术建议 |\n')
    f.write('|---|---------|------|------|------|---------|\n')
    for i, r in enumerate(p0_list[:50], 1):  # Show first 50
        f.write(f'| {i} | {r["name"][:30]}... | {r["industry"]} | {r["district"]} | {r["phone"][:15]}... | 重庆{r["industry"]}百度几乎无投放，{r["district"]}区域蓝海 |\n')
    if len(p0_list) > 50:
        f.write(f'\n> ... 共{len(p0_list)}家，详见JSON文件\n\n')
    
    f.write('## 📍 P1 近郊客户（次优拨打）\n\n')
    f.write('| # | 企业名称 | 行业 | 区域 | 电话 | 话术建议 |\n')
    f.write('|---|---------|------|------|------|---------|\n')
    for i, r in enumerate(p1_list[:30], 1):
        f.write(f'| {i} | {r["name"][:30]}... | {r["industry"]} | {r["district"]} | {r["phone"][:15]}... | 重庆{r["industry"]}百度几乎无投放，{r["district"]}区域蓝海 |\n')
    if len(p1_list) > 30:
        f.write(f'\n> ... 共{len(p1_list)}家，详见JSON文件\n\n')
    
    f.write('## 📍 P2 其他区县客户（补充拨打）\n\n')
    f.write('| # | 企业名称 | 行业 | 区域 | 电话 | 话术建议 |\n')
    f.write('|---|---------|------|------|------|---------|\n')
    for i, r in enumerate(p2_list[:20], 1):
        f.write(f'| {i} | {r["name"][:30]}... | {r["industry"]} | {r["district"]} | {r["phone"][:15]}... | 重庆{r["industry"]}百度几乎无投放，{r["district"]}区域蓝海 |\n')
    if len(p2_list) > 20:
        f.write(f'\n> ... 共{len(p2_list)}家，详见JSON文件\n\n')
    
    f.write('## 💡 拨打建议\n\n')
    f.write('1. **优先拨打P0**：主城区企业决策快，百度投放意愿高\n')
    f.write('2. **话术核心**：先问"你们在百度能搜到吗"，制造焦虑\n')
    f.write('3. **算账策略**：B2B制造业，投1万换10万订单\n')
    f.write('4. **记录要点**：痛点+当前获客方式+预算量级+决策人\n')

print(f'💾 Markdown report saved: {md_file}')

# Summary
print('\n' + '='*70)
print('[Call List Summary]')
print('='*70)
print(f'Total customers: {len(call_list)}')
print(f'P0 (Main urban): {len(p0_list)}')
print(f'P1 (Suburban): {len(p1_list)}')
print(f'P2 (Other districts): {len(p2_list)}')
print(f'\nFiles generated:')
print(f'  - JSON: {output_file}')
print(f'  - Markdown: {md_file}')

conn.close()
