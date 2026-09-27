#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""查询东财所有行业板块"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests
import json

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Referer': 'http://quote.eastmoney.com/'
})

# 行业板块: m:90 t:3
# 概念板块: m:90 t:2
for label, fs in [('行业板块', 'm:90 t:3'), ('概念板块(TOP50)', 'm:90 t:2')]:
    url = 'http://push2.eastmoney.com/api/qt/clist/get'
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
        'fields': 'f12,f14,f3,f62'
    }

    resp = session.get(url, params=params, timeout=15)
    data = resp.json()

    if data.get('data') and data['data'].get('diff'):
        items = data['data']['diff']
        print(f'\n{"="*50}')
        print(f'{label}: {len(items)}个')
        print(f'{"="*50}')
        for i, item in enumerate(items, 1):
            code = item.get('f12', '')
            name = item.get('f14', '')
            change = item.get('f3', 0) or 0
            if label.startswith('概念') and i > 50:
                break
            print(f'  {i:3d}. {code}  {name:12s}  {change:+.2f}%')
    else:
        print(f'\n{label}: 获取失败')
