# -*- coding: utf-8 -*-
"""扩展搜索GitHub工具"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests

print("=" * 70)
print("【扩展搜索 - 企业信息/电话获取工具】")
print("=" * 70)

queries = [
    'national enterprise credit information',
    'gsxt.gov.cn scraper',
    'chinamizhang company phone',
    '中国政府采购网 scraper',
    '招投标网站数据抓取',
    'companies house china',
    'business registration china api',
    'china enterprise data pipeline',
    'scraping chinese companies',
    'public company database china',
]

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
                desc = item.get('description', '无描述')[:60]
                url = item.get('html_url', '')
                print(f"  {i}. {name} ⭐{stars}")
                print(f"     {desc}...")
                print(f"     {url}")
        else:
            print("  无结果")
    except Exception as e:
        print(f"  错误: {e}")

print("\n" + "=" * 70)