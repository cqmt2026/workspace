# -*- coding: utf-8 -*-
"""北向资金 - 使用腾讯财经"""

import requests
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0'})

def fetch_north_flow_tencent():
    """腾讯财经北向资金数据"""
    
    # 腾讯 API: 沪深港通资金流
    url = 'http://stockapp.finance.qq.com/mstats/?id=sh_sz'
    
    try:
        resp = session.get(url, timeout=10)
        if resp.status_code == 200:
            content = resp.text
            
            # 尝试提取北向资金数据
            # 格式可能包含：北向资金净流入 XX 亿元
            pattern = r'北向.*?(\d+\.\d+) 亿元'
            matches = re.findall(pattern, content)
            
            if matches:
                print(f'OK 北向资金：{matches[0]}亿元')
                return matches[0]
            else:
                print('WARN 未找到北向资金数据')
                return None
        else:
            print(f'FAIL HTTP {resp.status_code}')
            return None
    except Exception as e:
        print(f'FAIL: {e}')
        return None


def fetch_north_flow_manual():
    """
    手动方式：从东财获取沪深股通个股资金流
    
    由于北向资金总览 API 不可用，我们通过统计沪深股通个股来估算
    """
    
    from pathlib import Path
    import json
    
    cookie_file = Path(__file__).parent.parent.parent / 'config' / 'eastmoney_cookie.json'
    with open(cookie_file, 'r', encoding='utf-8') as f:
        cookie = json.load(f)['cookie']
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0',
        'Cookie': cookie,
    })
    
    # 获取沪深股通前 10 大成交活跃股
    url = 'http://push2.eastmoney.com/api/qt/clist/get'
    params = {
        'pn': '1',
        'pz': '10',
        'fid': 'f184',  # 涨跌幅
        'po': '2',
        'fs': 'm:1 s:2',  # 沪深股通
        'fields': 'f12,f14,f62,f184'
    }
    
    print('获取沪深股通活跃股...')
    try:
        resp = session.get(url, params=params, timeout=10)
        data = resp.json()
        
        if data.get('data') and data['data'].get('diff'):
            items = data['data']['diff']
            print(f'OK 获取到 {len(items)} 只活跃股')
            
            # 计算总净流入 (简化估算)
            total_net = sum(item.get('f62', 0) for item in items) / 10000  # 亿元
            
            print(f'前 10 大活跃股总净流入：{total_net:.2f}亿元')
            print('个股明细:')
            for item in items[:5]:
                name = item.get('f14', '未知')
                net = item.get('f62', 0) / 10000
                pct = item.get('f184', 0)
                print(f'  {name}: {net:.2f}亿元 ({pct}%)')
            
            return total_net
        else:
            print('WARN 无数据')
            return None
    except Exception as e:
        print(f'FAIL: {e}')
        return None


if __name__ == '__main__':
    print('='*60)
    print('北向资金数据获取 (腾讯 + 东财)')
    print('='*60)
    print()
    
    print('[1] 腾讯财经...')
    fetch_north_flow_tencent()
    print()
    
    print('[2] 东财沪深股通...')
    fetch_north_flow_manual()
    print()
    
    print('='*60)
