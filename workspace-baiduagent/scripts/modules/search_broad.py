# -*- coding: utf-8 -*-
"""更广泛的搜索 - 企业数据获取"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests

queries = [
    # 政府公开数据
    'national enterprise credit system scraper',
    'china business registration public data',
    '企查查 开放平台 api',
    '天眼查 开放平台',
    
    # 数据聚合
    'company contact database china',
    'b2b lead generation china',
    'chinese business directory scraper',
    
    # 替代方案
    'scraping Chinese yellow pages',
    '中国黄页 数据抓取',
    '114电话查询 python',
    
    # 更通用的
    'phone number extraction python',
    'contact data enrichment',
]

print("=" * 70)
print("【广泛搜索 - 企业数据获取】")
print("=" * 70)

for query in queries:
    print(f"\n搜索: {query}")
    try:
        r = requests.get(
            'https://api.github.com/search/repositories',
            params={'q': query, 'per_page': 3, 'sort': 'stars'},
            timeout=15
        )
        data = r.json()
        items = data.get('items', [])
        if items:
            for i, item in enumerate(items[:2], 1):
                name = item.get('full_name', '')
                stars = item.get('stargazers_count', 0)
                desc = item.get('description', '无描述')[:70]
                url = item.get('html_url', '')
                print(f"  {i}. {name} ⭐{stars}")
                print(f"     {desc}...")
                print(f"     {url}")
        else:
            print("  无结果")
    except Exception as e:
        print(f"  错误: {e}")

print("\n" + "=" * 70)