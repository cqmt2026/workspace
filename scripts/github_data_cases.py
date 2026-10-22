#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""搜索GitHub数据可视化与政务数据商业化案例"""
import urllib.request
import json
import ssl
import urllib.parse
import sys

# 设置stdout编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def search_github(query, sort='stars', order='desc', per_page=10):
    """搜索GitHub仓库"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    encoded_query = urllib.parse.quote(query)
    url = f'https://api.github.com/search/repositories?q={encoded_query}&sort={sort}&order={order}&per_page={per_page}'
    
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/vnd.github.v3+json'
    })
    
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {'error': str(e)}

def main():
    queries = [
        'city data visualization dashboard',
        'government open data platform',
        'public data monetization',
        'data journalism visualization',
        'urban data storytelling',
    ]
    
    print('=' * 70)
    print('GitHub数据可视化与政务数据商业化案例调研')
    print('=' * 70)
    
    all_results = []
    
    for query in queries:
        print(f'\n[搜索: {query}]')
        data = search_github(query)
        
        if 'error' in data:
            print(f'  Error: {data["error"]}')
            continue
        
        items = data.get('items', [])
        total = data.get('total_count', 0)
        print(f'  Found {total} results')
        
        for i, item in enumerate(items[:5], 1):
            name = item["full_name"]
            stars = item["stargazers_count"]
            forks = item["forks_count"]
            desc = item.get("description") or "N/A"
            url = item["html_url"]
            lang = item.get("language") or "N/A"
            
            print(f'\n  {i}. {name}')
            print(f'     Stars: {stars} | Forks: {forks}')
            print(f'     {desc[:120]}...' if len(desc) > 120 else f'     {desc}')
            print(f'     URL: {url}')
            print(f'     Language: {lang}')
            all_results.append({
                'query': query,
                'name': name,
                'stars': stars,
                'desc': desc,
                'url': url,
                'lang': lang,
            })
    
    # Save results
    output_file = r'C:\Users\Administrator\.openclaw\workspace\memory\商业案例调研\github_data_cases.json'
    import os
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f'\n{"=" * 70}')
    print(f'Results saved to: {output_file}')
    print(f'Total projects: {len(all_results)}')

if __name__ == "__main__":
    main()
