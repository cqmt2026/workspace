# -*- coding: utf-8 -*-
import requests, sys
sys.stdout.reconfigure(encoding='utf-8')

print("=== 检测本机公网IP ===")
try:
    r = requests.get('https://httpbin.org/ip', timeout=10)
    print(f"公网IP: {r.json().get('origin')}")
except Exception as e:
    print(f"获取失败: {e}")
    try:
        r2 = requests.get('https://api.ipify.org?format=text', timeout=10)
        print(f"公网IP: {r2.text.strip()}")
    except Exception as e2:
        print(f"备用也失败: {e2}")
