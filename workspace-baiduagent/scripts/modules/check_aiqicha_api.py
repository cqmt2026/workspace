# -*- coding: utf-8 -*-
"""查询爱企查API文档"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests

print("=" * 70)
print("【爱企查API查询】")
print("=" * 70)

# 尝试访问爱企查开放平台
urls = [
    'https://aiqicha.baidu.com/devplatform',
    'https://aiqicha.baidu.com/api',
    'https://open.baidu.com/',
]

for url in urls:
    print(f"\n访问: {url}")
    try:
        r = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        print(f"  状态码: {r.status_code}")
        # 检查是否有API相关信息
        if 'api' in r.text.lower() or 'open' in r.text.lower() or 'developer' in r.text.lower():
            print(f"  ⚠️ 可能包含API信息")
    except Exception as e:
        print(f"  错误: {e}")

# 尝试直接调用爱企查搜索API
print(f"\n\n尝试直接调用搜索接口...")
try:
    r = requests.get(
        'https://aiqicha.baidu.com/s?q=科技有限公司&d=0',
        timeout=10,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    print(f"  状态码: {r.status_code}")
    print(f"  内容长度: {len(r.text)}")
    # 检查是否返回JSON数据
    if r.headers.get('content-type', '').startswith('application/json'):
        print(f"  ✅ 可能是API接口")
        print(f"  响应示例: {r.text[:200]}")
    else:
        print(f"  ❌ 返回的是HTML页面，不是API")
except Exception as e:
    print(f"  错误: {e}")

print("\n" + "=" * 70)