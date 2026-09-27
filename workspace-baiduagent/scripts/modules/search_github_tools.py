# -*- coding: utf-8 -*-
"""查询GitHub上的企业电话抓取工具"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests

print("=" * 70)
print("【GitHub工具搜索】")
print("=" * 70)

queries = [
    'china company phone extractor',
    '天眼查 python scraper',
    '企查查 api python',
    '企业数据抓取 python',
    'business info scraper china',
]

for query in queries:
    print(f"\n搜索: {query}")
    try:
        r = requests.get(
            'https://api.github.com/search/repositories',
            params={'q': query, 'per_page': 5, 'sort': 'stars'},
            timeout=15
        )
        data = r.json()
        items = data.get('items', [])
        if items:
            for i, item in enumerate(items[:3], 1):
                name = item.get('full_name', '')
                desc = item.get('description', '无描述')[:50]
                stars = item.get('stargazers_count', 0)
                url = item.get('html_url', '')
                print(f"  {i}. {name} - Stars:{stars}")
                print(f"     {desc}...")
                print(f"     {url}")
        else:
            print("  无结果")
    except Exception as e:
        print(f"  错误: {e}")

print("\n" + "=" * 70)
print("搜索完成")