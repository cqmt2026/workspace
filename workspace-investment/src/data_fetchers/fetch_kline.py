# -*- coding: utf-8 -*-
"""
获取历史 K 线数据
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
    config = json.load(f)
    cookie = config['cookie']

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Cookie': cookie,
    'Referer': 'https://www.eastmoney.com/'
})

def fetch_kline(code, klt='101', start_date='20240101', end_date='20260407'):
    """
    获取 K 线数据
    
    Args:
        code: 股票代码 (如 600519)
        klt: K 线类型 (101=日 K, 102=周 K, 103=月 K)
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        K 线数据列表
    """
    market = '1' if code.startswith('6') else '0'
    secid = f'{market}.{code}'
    
    url = 'http://push2his.eastmoney.com/api/qt/stock/kline/get'
    params = {
        'secid': secid,
        'klt': klt,
        'fqt': '1',  # 1=前复权，2=后复权，0=不复权
        'beg': start_date,
        'end': end_date,
        'fields': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61'  # 时间/开盘/收盘/最高/最低/成交量/成交额/振幅/涨跌幅/涨跌额/换手率
    }
    
    try:
        resp = session.get(url, params=params, timeout=15)
        data = resp.json()
        
        if data.get('data') and data['data'].get('klines'):
            klines = data['data']['klines']
            print(f'OK 获取到 {len(klines)} 条 K 线数据')
            
            # 解析前 5 条
            print('最近 5 个交易日:')
            for kl in klines[-5:]:
                parts = kl.split(',')
                date = parts[0]
                close = parts[2]
                pct = parts[8]
                print(f'  {date}: 收盘{close}元 ({pct}%)')
            
            return klines
        else:
            print(f'WARN 无 K 线数据')
            return []
    except Exception as e:
        print(f'FAIL: {e}')
        return []


if __name__ == '__main__':
    print('='*60)
    print('历史 K 线数据获取测试')
    print('='*60)
    print()
    
    # 测试 1: 日 K 线
    print('[1] 测试：日 K 线 (贵州茅台 600519)...')
    fetch_kline('600519', klt='101')
    print()
    
    # 测试 2: 周 K 线
    print('[2] 测试：周 K 线 (贵州茅台 600519)...')
    fetch_kline('600519', klt='102')
    print()
    
    # 测试 3: 月 K 线
    print('[3] 测试：月 K 线 (贵州茅台 600519)...')
    fetch_kline('600519', klt='103')
    print()
    
    # 测试 4: 其他股票
    print('[4] 测试：日 K 线 (平安银行 000001)...')
    fetch_kline('000001', klt='101')
    print()
    
    print('='*60)
    print('K 线数据获取完成')
    print('='*60)
