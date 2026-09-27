# -*- coding: utf-8 -*-
import sqlite3
import sys
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

db_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Target pool priority industries with specific keywords
target_industries = {
    '医疗器械': ['医疗科技', '生物科技', '医疗器械', '制药', 'IVD', '体外诊断', '海扶', '山外山', '中元汇吉', '登康口腔', '迈科唯', '博仕康', '贝奥新视野', '永仁心'],
    '新材料': ['新材料', '镁业', '钛业', '塑胶', '模具', '胶粘剂', '铝业', '秦河', '索创', '泰尔特'],
    '机械装备': ['机械', '起重', '模具', '精密', '传动', '切割', '激光', '豪能', '维大力', '星腾', '速能'],
    '环保检测': ['环保', '检测', '清洁', '春宇', '御澜泽', '恒之昇', '胜科', '书可'],
    '建筑建材': ['建筑', '建材', '装饰', '工程', '节能', '鹞鹏', '丰瀚', '聚鑫荣盛', '单轨', '创嘉泓'],
    '新能源': ['新能源', '充电桩', '充电设施', '特永', '壹木和', '铭和泰', '鑫牛', '国幸通', '雷能', '合晟', '四博电气', '熙腾']
}

# Get all A-class customers with phones
cursor.execute('''
    SELECT id, name, industry, phone, tier, district
    FROM customers
    WHERE tier = 'A' AND phone != '' AND phone IS NOT NULL
''')
all_a_customers = cursor.fetchall()

# Filter by target keywords and prioritize by industry
call_list = []
for cust in all_a_customers:
    cid, name, industry, phone, tier, district = cust
    
    # Check if name matches any target industry keywords
    matched_industry = None
    for ind, keywords in target_industries.items():
        if any(kw in name for kw in keywords):
            matched_industry = ind
            break
    
    if matched_industry:
        call_list.append((cid, name, matched_industry, phone, district))
    
    if len(call_list) >= 30:
        break

# Filter out those contacted in last 30 days
thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
cursor.execute('''
    SELECT DISTINCT customer_id 
    FROM call_logs 
    WHERE call_date >= ?
''', (thirty_days_ago,))
recently_contacted_ids = [row[0] for row in cursor.fetchall()]

# Remove recently contacted
filtered_list = [c for c in call_list if c[0] not in recently_contacted_ids]

conn.close()

# Sort by industry priority
industry_priority = {'医疗器械': 1, '新材料': 2, '机械装备': 3, '环保检测': 4, '建筑建材': 5, '新能源': 6}
filtered_list.sort(key=lambda x: (industry_priority.get(x[2], 99), x[1]))

# Generate call list with scripts
print('=' * 80)
print('今日拨打清单 - 2026年9月9日（周三）')
print('数据来源：中小客户目标池 + CRM精准匹配')
print('=' * 80)
print()

scripts = {
    '医疗器械': '老板好，我是百都科技的小度。注意到贵司在重庆医疗器械领域很有实力，但百度搜"重庆医疗器械""重庆IVD"，前十页都看不到你们。这意味着你们的客户找供应商时，第一个看到的是竞争对手。我们帮类似企业做百度精准获客，成本只有竞品的1/3。方便加个微信发您行业数据吗？',
    '新材料': '老板好，我是百都科技的小度。新材料行业百度基本是空白，贵司专精特新资质+技术实力，完全可以在百度上建立行业第一的认知。我们现在有新客户专享政策，首月低至3000元就能覆盖核心关键词。您方便了解一下吗？',
    '机械装备': '老板好，我是百都科技的小度。制造业企业客户找供应商，第一反应是百度搜。贵司产品这么好，但百度上搜不到，等于把客户拱手让给竞争对手。我们专注B2B精准获客，按线索付费，效果不好不收费。',
    '环保检测': '老板好，我是百都科技的小度。环保检测企业的主要客户是政府/国企，他们招标前一定会百度搜供应商名录。贵司现在百度上几乎是空白的，这是最大的获客机会。我们帮类似企业建立百度品牌曝光，月费3000起。',
    '建筑建材': '老板好，我是百都科技的小度。建筑工程B2B采购，百度是核心入口。贵司在百度上几乎没有投放，但搜索量很大。我们专注建材行业精准获客，按线索付费，效果不好不收钱。',
    '新能源': '老板好，我是百都科技的小度。新能源充电桩/设备制造商，百度竞争几乎为零。贵司产品有优势，但百度搜不到，等于错过大量B端客户。我们帮同类企业月均获取15+精准线索，成本仅300元/条。'
}

for i, c in enumerate(filtered_list[:10], 1):
    cid, name, industry, phone, district = c
    script = scripts.get(industry, scripts['其他'])
    
    print(f'{i}. {name}')
    print(f'   行业: {industry} | 电话: {phone} | 区域: {district if district else "未知"}')
    print(f'   话术: {script[:50]}...')
    print()

print('=' * 80)
print(f'共 {len(filtered_list[:10])} 家目标客户')
print('行业分布：')
from collections import Counter
ind_counts = Counter([c[2] for c in filtered_list[:10]])
for ind, count in ind_counts.most_common():
    print(f'  - {ind}: {count}家')
print()
print('提示：打电话时打开百度搜索结果页，实时展示"你们搜不到"')
print('=' * 80)
