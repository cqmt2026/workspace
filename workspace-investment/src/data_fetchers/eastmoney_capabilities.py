# -*- coding: utf-8 -*-
"""
东方财富 API 数据获取能力清单
"""

import requests
import json
from pathlib import Path
from datetime import datetime
import sys

# 设置 UTF-8 输出
sys.stdout.reconfigure(encoding='utf-8')

print('='*60)
print('东方财富 API 数据获取能力清单')
print('='*60)
print()

# 加载 Cookie
cookie_file = Path(__file__).parent.parent.parent / 'config' / 'eastmoney_cookie.json'
with open(cookie_file, 'r', encoding='utf-8') as f:
    config = json.load(f)
    cookie = config['cookie']

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Cookie': cookie,
    'Referer': 'https://www.eastmoney.com/'
})

capabilities = {}

# 【1】大盘指数
print('[1] 大盘指数...')
indices = [
    ('上证指数', '1.000001'),
    ('深证成指', '0.399001'),
    ('创业板指', '0.399006'),
    ('科创 50', '1.000688'),
]
ok_list = []

for name, secid in indices:
    url = 'http://push2.eastmoney.com/api/qt/stock/get'
    params = {'secid': secid, 'fields': 'f43'}
    try:
        resp = session.get(url, params=params, timeout=5)
        if resp.status_code == 200 and resp.json().get('data'):
            ok_list.append(name)
            print(f'  OK {name}')
    except:
        pass

capabilities['大盘指数'] = ok_list
print()

# 【2】个股行情
print('[2] 个股行情...')
ok_list = []
for code, name in [('600519', '贵州茅台'), ('000001', '平安银行')]:
    market = '1' if code.startswith('6') else '0'
    url = 'http://push2.eastmoney.com/api/qt/stock/get'
    params = {'secid': f'{market}.{code}', 'fields': 'f43'}
    try:
        resp = session.get(url, params=params, timeout=5)
        if resp.status_code == 200 and resp.json().get('data'):
            ok_list.append(name)
            print(f'  OK {name}')
    except:
        pass

capabilities['个股行情'] = ok_list
print()

# 【3】板块数据
print('[3] 板块数据...')
ok_list = []
for t, name in [('t:3', '概念板块'), ('t:2', '行业板块'), ('t:1', '地域板块')]:
    url = 'http://push2.eastmoney.com/api/qt/clist/get'
    params = {'pn': '1', 'pz': '10', 'fs': f'm:90 {t}', 'fields': 'f12,f14'}
    try:
        resp = session.get(url, params=params, timeout=10)
        if resp.status_code == 200 and resp.json().get('data'):
            ok_list.append(name)
            print(f'  OK {name}')
    except:
        pass

capabilities['板块数据'] = ok_list
print()

# 【4】资金流向
print('[4] 资金流向...')
ok_list = []
tests = [
    ('个股资金流', '1.600519', 'f113'),
    ('板块资金流', None, None),
]

for name, secid, field in tests:
    if secid:
        url = 'http://push2.eastmoney.com/api/qt/stock/get'
        params = {'secid': secid, 'fields': field}
    else:
        url = 'http://push2.eastmoney.com/api/qt/clist/get'
        params = {'pn': '1', 'pz': '10', 'fs': 'm:90 t:3', 'fields': 'f62'}
    
    try:
        resp = session.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            ok_list.append(name)
            print(f'  OK {name}')
    except:
        pass

capabilities['资金流向'] = ok_list
print()

# 【5】其他数据
print('[5] 其他数据...')
ok_list = []

# 历史 K 线
url = 'http://push2his.eastmoney.com/api/qt/stock/kline/get'
params = {'secid': '1.600519', 'klt': '101', 'beg': '20240101', 'end': '20260407'}
try:
    resp = session.get(url, params=params, timeout=15)
    if resp.status_code == 200 and resp.json().get('data'):
        ok_list.append('历史 K 线')
        print('  OK 历史 K 线')
except:
    pass

capabilities['其他数据'] = ok_list
print()

# 汇总
print('='*60)
print('数据获取能力汇总')
print('='*60)

for cat, items in capabilities.items():
    if items:
        print(f'\n{cat}:')
        for item in items:
            print(f'  OK {item}')

print(f'\n总计：{sum(len(v) for v in capabilities.values())} 个数据接口可用')
print('='*60)
