#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试sensenova API可用性"""
import urllib.request
import json
import sys

def main():
    # 读取配置
    with open(r'C:\Users\Administrator\.openclaw\openclaw.json', 'r', encoding='utf-8') as f:
        d = json.load(f)
    
    api_key = d['models']['providers']['sensenova']['apiKey']
    base_url = d['models']['providers']['sensenova']['baseUrl']
    
    print(f'=== 测试 sensenova API ===')
    print(f'Base URL: {base_url}')
    print(f'Key prefix: {api_key[:20]}...')
    print()
    
    # 测试模型列表
    print('1. 测试模型列表...')
    try:
        url = base_url + '/models'
        req = urllib.request.Request(url, headers={'Authorization': f'Bearer ***'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            print(f'   OK，{len(data.get("data", []))}个模型')
    except Exception as e:
        print(f'   Error: {e}')
    
    # 测试简单completion
    print('2. 测试chat/completions...')
    try:
        url = base_url + '/chat/completions'
        data = json.dumps({
            'model': 'deepseek-v4-flash',
            'messages': [{'role': 'user', 'content': 'hi'}],
            'max_tokens': 5
        }).encode()
        req = urllib.request.Request(url, data=data, headers={
            'Authorization': f'Bearer ***',
            'Content-Type': 'application/json'
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            print(f'   OK!')
            print(f"   回复: {result['choices'][0]['message']['content']}")
            print(f"   Token用量: {result['usage']}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f'   HTTP {e.code}: {body[:200]}')
    except Exception as e:
        print(f'   Error: {e}')
    
    # 测试Flash-Lite模型
    print('3. 测试Flash-Lite模型...')
    try:
        url = base_url + '/chat/completions'
        data = json.dumps({
            'model': 'sensenova-6.7-flash-lite',
            'messages': [{'role': 'user', 'content': 'hi'}],
            'max_tokens': 5
        }).encode()
        req = urllib.request.Request(url, data=data, headers={
            'Authorization': f'Bearer ***',
            'Content-Type': 'application/json'
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            print(f'   OK!')
            print(f"   回复: {result['choices'][0]['message']['content']}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f'   HTTP {e.code}: {body[:200]}')
    except Exception as e:
        print(f'   Error: {e}')

if __name__ == "__main__":
    main()
