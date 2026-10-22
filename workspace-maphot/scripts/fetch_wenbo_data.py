#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""获取文博场馆客流量数据"""
import urllib.request
import ssl
import json
import os
import time
import urllib.parse

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE_URL = 'https://data.dsjj.cq.gov.cn'

def fetch_json(url, params=None):
    """获取JSON数据"""
    try:
        url_full = BASE_URL + url
        if params:
            query = urllib.parse.urlencode(params)
            url_full = f'{url_full}?{query}'
        
        req = urllib.request.Request(url_full, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'X-Requested-With': 'XMLHttpRequest'
        })
        
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            data = resp.read().decode('utf-8', errors='ignore')
            if data.startswith('{') or data.startswith('['):
                return json.loads(data)
            return None
    except Exception as e:
        print(f'Error: {e}')
        return None

def main():
    print('=' * 70)
    print('文博场馆客流量数据获取')
    print('=' * 70)
    
    # 1. 尝试获取文旅委员会的数据集列表
    print('\n【步骤1】获取文旅委数据集...')
    
    apis = [
        '/opendata/api/dataset/list?orgCode=重庆市文化和旅游发展委员会&pageNo=1&pageSize=50',
        '/opendata/api/data/list?provider=重庆市文化和旅游发展委员会&page=1&limit=50',
        '/opendata/v1/dataset/list?department=文化&pageNo=1&pageSize=50',
    ]
    
    for api in apis:
        data = fetch_json(api)
        if data:
            print(f'SUCCESS: {api}')
            print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
            break
    
    # 2. 搜索文博相关数据
    print('\n【步骤2】搜索文博相关数据集...')
    search_apis = [
        '/opendata/api/dataset/search?keyword=文博&pageNo=1&pageSize=20',
        '/opendata/api/dataset/search?keyword=博物馆&pageNo=1&pageSize=20',
        '/opendata/api/dataset/search?keyword=客流&pageNo=1&pageSize=20',
    ]
    
    for api in search_apis:
        data = fetch_json(api)
        if data:
            print(f'SUCCESS: {api}')
            print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
            break
    
    # 3. 保存结果
    output_dir = r'C:\Users\Administrator\.openclaw\workspace\workspace-maphot\data'
    os.makedirs(output_dir, exist_ok=True)
    
    print('\n' + '=' * 70)
    print('提示: 该平台使用SPA架构，API端点需要进一步探索')
    print('建议: 手动在浏览器中打开数据集页面，F12查看Network面板')
    print('=' * 70)

if __name__ == "__main__":
    main()
