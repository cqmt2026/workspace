# -*- coding: utf-8 -*-
"""第一性原理验证：重新测试所有API配额状态"""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8')

GD_KEY = '3f85cf676f4eb0ccb2374560bb99bd51'
TX_KEY = 'JGGBZ-D5I6Q-66H5K-22SMU-I5VXO-NDFLJ'
BD_KEY = 'KKcT6s3E4l3z3cY2i2C0'  # 需要完整Key

print("=" * 60)
print("【假设验证】重新测试所有API")
print("=" * 60)

# 测试1: 腾讯geocoder是否真的可用（连续10次）
print("\n1. 腾讯 geocoder (连续10次测试)")
for i in range(10):
    r = requests.get('https://apis.map.qq.com/ws/geocoder/v1',
        params={'key': TX_KEY, 'address': f'重庆市测试{i}号', 'region': '重庆'}, timeout=5)
    d = r.json()
    if d.get('status') != 0:
        print(f"   第{i+1}次: FAIL {d.get('message')}")
        break
    if i == 9:
        print("   10次全部成功 - geocoder配额充足")

# 测试2: 腾讯place是否真的超限
print("\n2. 腾讯 place/search (测试1次)")
r = requests.get('https://apis.map.qq.com/ws/place/v1/search',
    params={'key': TX_KEY, 'boundary': 'region(重庆,0)', 'keyword': '口腔', 'max_per_page': 3}, timeout=5)
d = r.json()
print(f"   status={d.get('status')}, msg={d.get('message','')}")

# 测试3: 高德around为什么报INVALID_USER_KEY
print("\n3. 高德 around (测试1次)")
r = requests.get('https://restapi.amap.com/v3/place/around',
    params={'keywords': '口腔', 'location': '106.55,29.56', 'radius': 5000, 'offset': 5, 'page': 1, 'key': GD_KEY}, timeout=5)
d = r.json()
print(f"   status={d.get('status')}, info={d.get('info')}")
if d.get('info') == 'INVALID_USER_KEY':
    print("   -> 这是Key无效，不是配额问题！")

# 测试4: 高德text的配额状态
print("\n4. 高德 text (测试1次)")
r = requests.get('https://restapi.amap.com/v3/place/text',
    params={'keywords': '口腔', 'city': '重庆', 'offset': 5, 'page': 1, 'key': GD_KEY}, timeout=5)
d = r.json()
print(f"   status={d.get('status')}, info={d.get('info')}")

print("\n" + "=" * 60)
print("【关键发现】")
print("=" * 60)
print("1. 腾讯 geocoder 是否真的无限制？")
print("2. 高德 around 的 INVALID_USER_KEY 说明Key配置有问题")
print("3. 需要区分'配额超限'和'Key无效'两种错误")
