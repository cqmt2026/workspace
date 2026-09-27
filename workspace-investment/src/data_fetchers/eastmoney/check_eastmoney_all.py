#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""深度查询东财所有板块分类体系"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests
import json

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Referer': 'http://quote.eastmoney.com/'
})

url = 'http://push2.eastmoney.com/api/qt/clist/get'

# 东财板块分类:
# m:90 t:1 - 地域板块
# m:90 t:2 - 行业板块(细分)
# m:90 t:3 - 概念板块
# m:1 t:2 - 沪A
# m:0 t:6 - 深A
# m:90 t:1 f:!50 - 地域(排除ST)

categories = [
    ('地域板块', 'm:90 t:1'),
    ('行业板块(t:2)', 'm:90 t:2'),
    ('概念板块(t:3)', 'm:90 t:3'),
]

for label, fs in categories:
    params = {
        'pn': '1',
        'pz': '500',
        'po': '1',
        'np': '1',
        'ut': 'bd1d9ddb04089700cf3c27f2ee54499e',
        'fltt': '2',
        'invt': '2',
        'fid': 'f3',
        'fs': fs,
        'fields': 'f12,f14,f3,f104,f105'  # f104=上涨家数 f105=下跌家数
    }

    try:
        resp = session.get(url, params=params, timeout=15)
        data = resp.json()

        if data.get('data') and data['data'].get('diff'):
            items = data['data']['diff']
            print(f'\n{"="*60}')
            print(f'{label}: 共 {len(items)} 个')
            print(f'{"="*60}')
            for i, item in enumerate(items, 1):
                code = item.get('f12', '')
                name = item.get('f14', '')
                change = item.get('f3', 0) or 0
                up = item.get('f104', 0) or 0
                down = item.get('f105', 0) or 0
                total = up + down
                print(f'  {i:3d}. {code}  {name:14s}  {change:+6.2f}%  成分股:{total:4d}')
        else:
            print(f'\n{label}: 无数据')
    except Exception as e:
        print(f'\n{label}: 错误 {e}')

# 再查一下申万行业分类
print(f'\n{"="*60}')
print('额外: 申万一级行业(m:90 t:2 按成分股数排序)')
print(f'{"="*60}')
params = {
    'pn': '1',
    'pz': '100',
    'po': '1',
    'np': '1',
    'ut': 'bd1d9ddb04089700cf3c27f2ee54499e',
    'fltt': '2',
    'invt': '2',
    'fid': 'f20',  # 按总市值排序
    'fs': 'm:90 t:2',
    'fields': 'f12,f14,f3,f104,f105,f20'
}
try:
    resp = session.get(url, params=params, timeout=15)
    data = resp.json()
    if data.get('data') and data['data'].get('diff'):
        items = data['data']['diff']
        for i, item in enumerate(items, 1):
            code = item.get('f12', '')
            name = item.get('f14', '')
            change = item.get('f3', 0) or 0
            up = item.get('f104', 0) or 0
            down = item.get('f105', 0) or 0
            total = up + down
            mcap = item.get('f20', 0) or 0
            mcap_yi = mcap / 100000000 if mcap > 0 else 0
            print(f'  {i:3d}. {code}  {name:14s}  {change:+6.2f}%  成分股:{total:4d}  市值:{mcap_yi:.0f}亿')
except Exception as e:
    print(f'  错误: {e}')
