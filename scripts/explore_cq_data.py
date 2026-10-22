#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探索重庆市公共数据开放系统"""
import urllib.request
import ssl
import json
import re

def fetch_url(url):
    """获取URL内容"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/json',
        'Accept-Language': 'zh-CN,zh;q=0.9'
    })
    
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            return resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return f"Error: {e}"

def main():
    base_url = 'https://data.dsjj.cq.gov.cn'
    
    print('=' * 70)
    print('重庆市公共数据开放系统探索')
    print('=' * 70)
    
    # 1. 访问首页
    print('\n【1. 首页分析】')
    html = fetch_url(f'{base_url}/opendata/home')
    print(f'页面大小: {len(html)} bytes')
    
    # 提取标题
    title_match = re.search(r'<title>([^<]+)</title>', html)
    if title_match:
        print(f'标题: {title_match.group(1)}')
    
    # 查找所有链接
    links = re.findall(r'href=["\']([^"\']+)["\']', html)
    print(f'\n发现 {len(links)} 个链接:')
    for link in set(links[:30]):
        if link.startswith('http') or link.startswith('/'):
            print(f'  {link}')
    
    # 2. 尝试常见API端点
    print('\n【2. API端点测试】')
    apis = [
        '/opendata/api/dataset/list',
        '/opendata/api/data/resources',
        '/opendata/interface',
        '/api/v1/datasets',
        '/api/datasets',
    ]
    
    for api in apis:
        content = fetch_url(f'{base_url}{api}')
        if 'Error' in content:
            print(f'{api}: {content}')
        else:
            # 检查是否是JSON
            try:
                data = json.loads(content)
                print(f'{api}: JSON ({len(content)} bytes)')
                if isinstance(data, dict):
                    print(f'  Keys: {list(data.keys())[:10]}')
                elif isinstance(data, list):
                    print(f'  Items: {len(data)}')
            except:
                print(f'{api}: HTML ({len(content)} bytes)')
    
    # 3. 查找JavaScript中的API调用
    print('\n【3. JavaScript中的API】')
    js_apis = re.findall(r'[\"\']([^\"\']*(?:api|interface|dataset|resource)[^\"\']*)[\"\']', html, re.IGNORECASE)
    for api in set(js_apis[:20]):
        print(f'  {api}')
    
    # 4. 查找表单和搜索功能
    print('\n【4. 搜索/筛选功能】')
    forms = re.findall(r'<form[^>]*action=["\']([^"\']+)["\'][^>]*>', html, re.IGNORECASE)
    for form in forms[:10]:
        print(f'  Form action: {form}')
    
    inputs = re.findall(r'<input[^>]*name=["\']([^"\']+)["\'][^>]*>', html)
    if inputs:
        print(f'  Input names: {set(inputs[:20])}')

if __name__ == "__main__":
    main()
