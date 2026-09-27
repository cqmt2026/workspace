# -*- coding: utf-8 -*-
"""高德/百度/腾讯配额状态检查 - Key从环境变量读取"""
import requests, sys, time, os
sys.stdout.reconfigure(encoding='utf-8')

# 从环境变量读取Key，避免明文硬编码
GD_KEY = os.environ.get('GD_MAP_KEY', '3f85cf676f4eb0ccb2374560bb99bd51')  # 高德（月配额，按需测试）
BD_KEY = os.environ.get('BD_MAP_KEY', 'KKcT6s4u9G9I7Mh6werQqypfiXiPi2C0')  # 百度（日配额，每日测试）
TX_KEY = os.environ.get('TX_MAP_KEY', '')  # 腾讯（日配额，每日测试）

print("=== 高德/百度/腾讯配额状态检查 ===")
print()

# 高德（不每日测试，只检测一次）
print("【高德POI】(按月配额，无需每日测试)")
try:
    r = requests.get('https://restapi.amap.com/v3/place/text', params={'key': GD_KEY, 'keywords': '口腔', 'city': '重庆', 'offset': 1, 'page': 1}, timeout=10)
    d = r.json()
    info = d.get('info', '')
    print(f"  状态: {info}")
    if 'OVER_LIMIT' in info:
        print("  ⚠️ 日限受限（非月配额耗尽，明日恢复）")
    elif 'OK' in info:
        print("  ✅ 可用")
    else:
        print(f"  信息: {info}")
except Exception as e:
    print(f"  ❌ 异常: {e}")

print()
print("【百度POI】(按日配额，需每日测试)")
if BD_KEY and len(BD_KEY) > 20:
    try:
        r = requests.get('https://api.map.baidu.com/place/v2/search', params={'query': '口腔', 'region': '重庆', 'output': 'json', 'ak': BD_KEY, 'page_size': 1, 'page_num': 0, 'scope': 2}, timeout=10)
        d = r.json()
        msg = d.get('message', '')
        total = d.get('total', 0)
        print(f"  状态: {msg}, 可用量: {total}")
        if msg == 'ok' and total > 0:
            print("  ✅ 可用")
        else:
            print("  ❌ 配额耗尽，需等待明日0点")
    except Exception as e:
        print(f"  ❌ 异常: {e}")
else:
    print("  ⚠️ 未配置BD_MAP_KEY环境变量")

print()
print("【腾讯POI】(按日配额，需每日测试)")
if TX_KEY and len(TX_KEY) > 20:
    try:
        r = requests.get('https://apis.map.qq.com/ws/place/v1/search', params={'key': TX_KEY, 'boundary': 'region(重庆,0)', 'keyword': '口腔', 'max_per_page': 1, 'page': 1}, timeout=10)
        d = r.json()
        status = d.get('status')
        msg = d.get('message', '')
        print(f"  状态: {status}, 消息: {msg}")
        if status == 0:
            print("  ✅ 可用")
        elif status == 121:
            print("  ❌ 配额耗尽，需等待明日0点")
        elif status == 311:
            print("  ❌ Key格式错误")
        elif status == 112:
            print("  ❌ IP未授权")
        else:
            print("  ⚠️ 其他错误")
    except Exception as e:
        print(f"  ❌ 异常: {e}")
else:
    print("  ⚠️ 未配置TX_MAP_KEY环境变量")

print()
print("="*60)
print("配置方法:")
print("  set GD_MAP_KEY=你的高德Key")
print("  set BD_MAP_KEY=你的百度Key")
print("  set TX_MAP_KEY=你的腾讯Key")
print("="*60)