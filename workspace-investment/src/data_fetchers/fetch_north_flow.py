# -*- coding: utf-8 -*-
"""
获取北向资金流向数据
"""

import requests
import json
from pathlib import Path
from datetime import datetime
import sys

sys.stdout.reconfigure(encoding='utf-8')

# 加载 Cookie
cookie_file = Path(__file__).parent.parent.parent / 'config' / 'eastmoney_cookie.json'
with open(cookie_file, 'r', encoding='utf-8') as f:
    cookie = json.load(f)['cookie']

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Cookie': cookie,
    'Referer': 'https://www.eastmoney.com/'
})

def fetch_north_flow():
    """获取北向资金实时数据"""
    
    # API 1: 沪深港通资金流
    url = 'http://push2.eastmoney.com/api/qt/stock/get'
    params = {
        'secid': '1.A20093',  # 北向资金
        'fields': 'f113,f114,f115,f116,f117,f124'
    }
    
    print('[1] 东财 API 测试...')
    try:
        resp = session.get(url, params=params, timeout=10)
        data = resp.json()
        
        if data.get('data'):
            d = data['data']
            net = d.get('f113', 0) / 10000  # 亿元
            buy = d.get('f114', 0) / 10000  # 亿元
            sell = d.get('f115', 0) / 10000  # 亿元
            
            print(f'  OK 北向资金:')
            print(f'    净流入：{net:.2f}亿元')
            print(f'    买入：{buy:.2f}亿元')
            print(f'    卖出：{sell:.2f}亿元')
            return {'net': net, 'buy': buy, 'sell': sell}
        else:
            print(f'  WARN 无数据 (API 可能不支持)')
    except Exception as e:
        print(f'  FAIL: {e}')
    
    # API 2: 资金流排行榜
    print()
    print('[2] 资金流排行榜...')
    url = 'http://push2.eastmoney.com/api/qt/clist/get'
    params = {
        'pn': '1',
        'pz': '10',
        'fid': 'f62',  # 主力净流入
        'po': '2',  # 降序
        'fs': 'm:1 s:2',  # 沪深股通
        'fields': 'f12,f14,f62,f184'
    }
    
    try:
        resp = session.get(url, params=params, timeout=10)
        data = resp.json()
        
        if data.get('data') and data['data'].get('diff'):
            items = data['data']['diff']
            print(f'  OK 获取到 {len(items)} 只沪深股通股票')
            print('  主力净流入前 5:')
            for item in items[:5]:
                name = item.get('f14', '未知')
                net = item.get('f62', 0) / 10000  # 亿元
                ratio = item.get('f184', 0)
                print(f'    {name}: {net:.2f}亿元 ({ratio}%)')
            return items
        else:
            print(f'  WARN 无数据')
    except Exception as e:
        print(f'  FAIL: {e}')
    
    return None


if __name__ == '__main__':
    print('='*60)
    print('北向资金流向数据获取')
    print('='*60)
    print()
    
    fetch_north_flow()
    
    print()
    print('='*60)
    print('测试完成')
    print('='*60)
