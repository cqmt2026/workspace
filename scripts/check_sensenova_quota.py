#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查询sensenova额度信息"""
import urllib.request
import json
import re
import http.cookiejar

def fetch_sensenova_console():
    """访问sensenova控制台"""
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    
    url = 'https://platform.sensenova.cn/console'
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'zh-CN,zh;q=0.9'
    })
    
    try:
        with opener.open(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            print(f'页面大小: {len(html)} bytes')
            
            # 查找额度相关信息
            patterns = [
                r'额度[:\s]*([\d,\.]+)',
                r'配额[:\s]*([\d,\.]+)',
                r'quota[:\s]*([\d,\.]+)',
                r'balance[:\s]*([\d,\.]+)',
                r'剩余[:\s]*([\d,\.]+)',
                r'使用量[:\s]*([\d,\.]+)',
                r'token[:\s]*([\d,\.]+)',
            ]
            
            found = False
            for pat in patterns:
                matches = re.findall(pat, html, re.IGNORECASE)
                if matches:
                    found = True
                    print(f'\n找到{pat}:')
                    for m in matches[:10]:
                        print(f'  {m}')
            
            if not found:
                print('\n未找到明显的额度信息，页面可能是SPA（单页应用）')
                
            return html
    except Exception as e:
        print(f'错误: {e}')
        return None

def test_api_endpoints():
    """测试API端点"""
    # 读取配置
    with open(r'C:\Users\Administrator\.openclaw\openclaw.json', 'r', encoding='utf-8') as f:
        d = json.load(f)
    
    api_key = d['models']['providers']['sensenova']['apiKey']
    base_url = d['models']['providers']['sensenova']['baseUrl']
    
    print(f'\n测试API: {base_url}')
    
    endpoints = [
        '/v1/user/balance',
        '/v1/credits',
        '/v1/usage',
        '/v1/quota',
        '/user/balance',
        '/credits',
        '/usage',
        '/quota',
    ]
    
    for ep in endpoints:
        try:
            url = base_url + ep
            req = urllib.request.Request(url, headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            })
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = resp.read().decode()
                print(f'{ep}: OK - {data[:200]}')
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:200]
            print(f'{ep}: HTTP {e.code} - {body}')
        except Exception as e:
            print(f'{ep}: Error - {str(e)[:100]}')

if __name__ == "__main__":
    print("=== 查询sensenova额度 ===\n")
    fetch_sensenova_console()
    test_api_endpoints()
