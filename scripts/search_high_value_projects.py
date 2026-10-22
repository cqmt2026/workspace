#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""搜索高价值数据可视化项目"""
import urllib.request
import json
import ssl
import urllib.parse
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def search_github(query, sort='stars', order='desc', per_page=10, min_stars=500):
    """搜索GitHub仓库"""
    encoded_query = urllib.parse.quote(query)
    url = f'https://api.github.com/search/repositories?q={encoded_query}&sort={sort}&order={order}&per_page={per_page}'
    
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/vnd.github.v3+json'
    })
    
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            data = json.loads(resp.read())
            # 过滤低于min_stars的项目
            items = [i for i in data.get('items', []) if i.get('stargazers_count', 0) >= min_stars]
            return {'total': data.get('total_count', 0), 'items': items[:5]}
    except Exception as e:
        return {'error': str(e), 'items': []}

def get_repo_details(full_name):
    """获取仓库详细信息"""
    url = f'https://api.github.com/repos/{full_name}'
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/vnd.github.v3+json'
    })
    try:
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            return json.loads(resp.read())
    except:
        return None

def main():
    queries = [
        ('data visualization dashboard', 1000),
        ('open data platform', 500),
        ('government data dashboard', 500),
        ('city information system', 500),
        ('realtime data monitoring', 500),
        ('geospatial visualization', 500),
        ('public sector data', 300),
    ]
    
    print('=' * 80)
    print('高价值数据可视化项目搜索 (Stars >= 阈值)')
    print('=' * 80)
    
    all_results = []
    
    for query, min_stars in queries:
        print(f'\n[搜索: {query}] (最低⭐{min_stars})')
        data = search_github(query, min_stars=min_stars)
        
        if 'error' in data:
            print(f'  错误: {data["error"]}')
            continue
        
        print(f'  总结果: {data["total"]}')
        
        for i, item in enumerate(data['items'], 1):
            stars = item['stargazers_count']
            desc = item.get('description') or 'N/A'
            lang = item.get('language') or 'N/A'
            
            print(f'\n  {i}. {item["full_name"]} ⭐{stars}')
            print(f'     语言: {lang} | Forks: {item["forks_count"]}')
            print(f'     {desc[:100]}...' if len(desc) > 100 else f'     {desc}')
            
            all_results.append({
                'query': query,
                'name': item['full_name'],
                'stars': stars,
                'desc': desc,
                'lang': lang,
                'url': item['html_url'],
            })
    
    # 保存结果
    output_file = r'C:\Users\Administrator\.openclaw\workspace\memory\商业案例调研\high_value_projects.json'
    import os
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f'\n{"=" * 80}')
    print(f'共找到 {len(all_results)} 个高价值项目')
    print(f'结果已保存至: {output_file}')

if __name__ == "__main__":
    main()
