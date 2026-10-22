#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""获取重庆市公共数据开放平台数据集"""
import urllib.request
import json
import ssl
import os
import time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE_URL = 'https://data.dsjj.cq.gov.cn'

def fetch_json(url, params=None, retries=3):
    """获取JSON数据"""
    for i in range(retries):
        try:
            url_with_params = url
            if params:
                query = '&'.join([f'{k}={v}' for k, v in params.items()])
                url_with_params = f'{url}?{query}'
            
            req = urllib.request.Request(url_with_params, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9'
            })
            
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                return json.loads(resp.read().decode('utf-8', errors='ignore'))
        except Exception as e:
            print(f'  重试 {i+1}/{retries}: {e}')
            time.sleep(1)
    return None

def get_catalog():
    """获取数据目录"""
    print('\n【获取数据目录】')
    
    # 尝试不同的API端点
    endpoints = [
        '/opendata/api/dataset/catalog',
        '/opendata/api/data/catalog',
        '/opendata/v1/dataset/list',
        '/opendata/v1/datasets',
    ]
    
    for endpoint in endpoints:
        print(f'\n尝试: {endpoint}')
        data = fetch_json(BASE_URL + endpoint)
        if data and isinstance(data, dict):
            print(f'  成功! Keys: {list(data.keys())[:10]}')
            return data
        elif data and isinstance(data, list):
            print(f'  成功! 列表长度: {len(data)}')
            return data
    
    return None

def search_datasets(keyword, page=1, size=20):
    """搜索数据集"""
    print(f'\n【搜索数据集: {keyword}】')
    
    # 尝试搜索API
    endpoints = [
        f'/opendata/api/dataset/search?keyword={keyword}&page={page}&size={size}',
        f'/opendata/api/data/search?keyword={keyword}&page={page}&size={size}',
        f'/opendata/v1/dataset/search?keyword={keyword}',
    ]
    
    for endpoint in endpoints:
        data = fetch_json(BASE_URL + endpoint)
        if data:
            print(f'  成功!')
            return data
        else:
            print(f'  失败: {endpoint}')
    
    return None

def get_dataset_detail(dataset_id):
    """获取数据集详情"""
    print(f'\n【获取数据集详情: {dataset_id}】')
    
    endpoints = [
        f'/opendata/api/dataset/{dataset_id}',
        f'/opendata/v1/dataset/{dataset_id}',
        f'/opendata/dataset/detail?id={dataset_id}',
    ]
    
    for endpoint in endpoints:
        data = fetch_json(BASE_URL + endpoint)
        if data:
            print(f'  成功!')
            return data
    
    return None

def main():
    print('=' * 70)
    print('重庆市公共数据开放平台 - 数据获取测试')
    print('=' * 70)
    
    # 1. 获取目录
    catalog = get_catalog()
    
    if catalog:
        # 保存catalog
        output_file = r'C:\Users\Administrator\.openclaw\workspace\memory\商业案例调研\cq_data_catalog.json'
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)
        print(f'\n已保存至: {output_file}')
    
    # 2. 搜索热门数据集
    keywords = ['交通', '旅游', '文化', '教育', '气象', '人口']
    
    all_datasets = []
    for keyword in keywords:
        datasets = search_datasets(keyword)
        if datasets and isinstance(datasets, list):
            all_datasets.extend(datasets[:5])
        time.sleep(0.5)  # 避免请求过快
    
    if all_datasets:
        print(f'\n共获取 {len(all_datasets)} 个数据集')
        
        # 保存搜索结果
        output_file = r'C:\Users\Administrator\.openclaw\workspace\memory\商业案例调研\cq_data_search.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_datasets, f, indent=2, ensure_ascii=False)
        print(f'已保存至: {output_file}')
    
    print('\n' + '=' * 70)

if __name__ == "__main__":
    main()
