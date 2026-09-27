# -*- coding: utf-8 -*-
"""获取 K 线数据 - 使用腾讯财经 API"""

import requests
from datetime import datetime
import sys

sys.stdout.reconfigure(encoding='utf-8')

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0'})

def fetch_kline_tencent(code, market='sh'):
    """
    腾讯财经 K 线数据
    格式：http://data.gtimg.cn/flashdata/hushen/minute/sh600519.js
    """
    
    # 腾讯 API
    url = f'http://data.gtimg.cn/flashdata/hushen/minute/{market}{code}.js'
    
    try:
        resp = session.get(url, timeout=10)
        if resp.status_code == 200:
            # 响应格式：_sh600519="..."
            content = resp.text.strip()
            if content and '=' in content:
                data_str = content.split('="')[1].rstrip('";')
                print(f'OK 获取到数据')
                print(f'数据前 200 字：{data_str[:200]}')
                return data_str
            else:
                print(f'WARN 数据格式异常')
                return None
        else:
            print(f'FAIL HTTP {resp.status_code}')
            return None
    except Exception as e:
        print(f'FAIL: {e}')
        return None


if __name__ == '__main__':
    print('='*60)
    print('腾讯财经 K 线数据测试')
    print('='*60)
    print()
    
    print('[1] 测试：贵州茅台 (600519)...')
    fetch_kline_tencent('600519', market='sh')
    print()
    
    print('[2] 测试：平安银行 (000001)...')
    fetch_kline_tencent('000001', market='sz')
    print()
    
    print('='*60)
