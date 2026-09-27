# -*- coding: utf-8 -*-
"""
获取龙虎榜数据
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

def fetch_top_list(date=None):
    """
    获取龙虎榜数据
    
    Args:
        date: 日期 (YYYYMMDD), 默认今天
    """
    if not date:
        date = datetime.now().strftime('%Y%m%d')
    
    # 东财龙虎榜 API
    url = 'http://push2.eastmoney.com/api/qt/clist/get'
    params = {
        'pn': '1',
        'pz': '20',
        'fid': 'f62',  # 主力净流入
        'po': '2',  # 降序
        'fs': 'm:0 t:6,m:0 t:80,m:1 t:2',  # 全部 A 股
        'fields': 'f12,f14,f3,f62,f184,f46'
    }
    
    print(f'获取龙虎榜 ({date})...')
    
    try:
        resp = session.get(url, params=params, timeout=15)
        data = resp.json()
        
        if data.get('data') and data['data'].get('diff'):
            items = data['data']['diff']
            print(f'OK 获取到 {len(items)} 只股票')
            
            # 显示前 10 大主力净流入
            print('主力净流入前 10:')
            for i, item in enumerate(items[:10], 1):
                code = item.get('f12', '')
                name = item.get('f14', '')
                pct = item.get('f3', 0)  # 涨跌幅
                net = item.get('f62', 0) / 10000  # 主力净流入 (亿元)
                ratio = item.get('f184', 0)  # 主力净流入占比
                
                print(f'  {i}. {name} ({code}): {pct}% 主力{net:.2f}亿 ({ratio}%)')
            
            return items
        else:
            print('WARN 无数据')
            return []
    except Exception as e:
        print(f'FAIL: {e}')
        return []


if __name__ == '__main__':
    print('='*60)
    print('龙虎榜数据获取')
    print('='*60)
    print()
    
    fetch_top_list()
    
    print()
    print('='*60)
    print('测试完成')
    print('='*60)
