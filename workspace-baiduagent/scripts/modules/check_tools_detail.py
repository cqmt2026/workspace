# -*- coding: utf-8 -*-
"""查看具体工具详情"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests

repos = [
    'wangyeyu2016/Python_Crawler_Tianyancha',
    'iamsk/tianyancha',
    'YunCan-code/TianYanChaSpider',
    'YangAi/china-company-database',
    'lundbird/Chinese-Financial-WebScraper',
]

print("=" * 70)
print("【工具详情】")
print("=" * 70)

for repo in repos:
    print(f"\n{repo}")
    try:
        r = requests.get(f'https://api.github.com/repos/{repo}', timeout=15)
        data = r.json()
        if r.status_code == 200:
            desc = data.get('description', '无描述')
            stars = data.get('stargazers_count', 0)
            lang = data.get('language', '未知')
            topics = ', '.join(data.get('topics', []))[:100]
            url = data.get('html_url', '')
            print(f"  Stars: {stars} | 语言: {lang}")
            print(f"  描述: {desc}")
            print(f"  标签: {topics}")
            print(f"  链接: {url}")
            
            # 查看README
            if 'readme' in data:
                print(f"  README: {data['readme']}")
        else:
            print(f"  错误: {r.status_code}")
    except Exception as e:
        print(f"  错误: {e}")

print("\n" + "=" * 70)